import linecache
import os.path
import re
import sys
import traceback  # @Reimport

from _pydev_bundle import pydev_log
from _pydevd_bundle import pydevd_dont_trace
from _pydevd_bundle import pydevd_vars
from _pydevd_bundle.pydevd_breakpoints import get_exception_breakpoint
from _pydevd_bundle.pydevd_comm import CMD_STEP_CAUGHT_EXCEPTION, CMD_STEP_RETURN, CMD_STEP_OVER, CMD_SET_BREAK, \
    CMD_STEP_INTO, CMD_SMART_STEP_INTO, CMD_RUN_TO_LINE, CMD_SET_NEXT_STATEMENT, CMD_STEP_INTO_MY_CODE
from _pydevd_bundle.pydevd_constants import STATE_SUSPEND, dict_contains, get_thread_id, STATE_RUN, dict_iter_values, IS_PY3K, \
    dict_keys, dict_pop, RETURN_VALUES_PREFIX
from _pydevd_bundle.pydevd_dont_trace_files import DONT_TRACE, PYDEV_FILE
from _pydevd_bundle.pydevd_frame_utils import add_exception_to_frame, just_raised
from pydevd_file_utils import get_abs_path_real_path_and_base_from_frame

try:
    from inspect import CO_GENERATOR
except:
    CO_GENERATOR = 0

try:
    from _pydevd_bundle.pydevd_signature import send_signature_call_trace, send_signature_return_trace
except ImportError:
    def send_signature_call_trace(*args, **kwargs):
        pass

basename = os.path.basename

IGNORE_EXCEPTION_TAG = re.compile('[^#]*#.*@IgnoreException')
DEBUG_START = ('pydevd.py', 'run')
DEBUG_START_PY3K = ('_pydev_execfile.py', 'execfile')
TRACE_PROPERTY = 'pydevd_traceproperty.py'
get_file_type = DONT_TRACE.get


#=======================================================================================================================
# PyDBFrame
#=======================================================================================================================
class PyDBFrame: # No longer cdef because object was dying when only a reference to trace_dispatch was kept (need to check alternatives).
    '''This makes the tracing for a given frame, so, the trace_dispatch
    is used initially when we enter into a new context ('call') and then
    is reused for the entire context.
    '''

    #Note: class (and not instance) attributes.

    #Same thing in the main debugger but only considering the file contents, while the one in the main debugger
    #considers the user input (so, the actual result must be a join of both).
    filename_to_lines_where_exceptions_are_ignored = {}
    filename_to_stat_info = {}
    should_skip = -1

    # IFDEF CYTHON
    # def __init__(self, args):
        # self._args = args # In the cython version we don't need to pass the frame
    # ELSE
    def __init__(self, args):
        #args = main_debugger, filename, base, info, t, frame
        #yeap, much faster than putting in self and then getting it from self later on
        self._args = args[:-1] # Remove the frame (we don't want to have a reference to it).
    # ENDIF

    def set_suspend(self, *args, **kwargs):
        self._args[0].set_suspend(*args, **kwargs)

    def do_wait_suspend(self, *args, **kwargs):
        self._args[0].do_wait_suspend(*args, **kwargs)

    # IFDEF CYTHON
    # def trace_exception(self, frame, str event, arg):
    #     cdef bint flag;
    # ELSE
    def trace_exception(self, frame, event, arg):
    # ENDIF
        if event == 'exception':
            flag, frame = self.should_stop_on_exception(frame, event, arg)

            if flag:
                self.handle_exception(frame, event, arg)
                return self.trace_dispatch

        return self.trace_exception

    def trace_return(self, frame, event, arg):
        if event == 'return':
            main_debugger, filename, info, thread = self._args
            send_signature_return_trace(main_debugger, frame, filename, arg)
        return self.trace_return

    # IFDEF CYTHON
    # def should_stop_on_exception(self, frame, str event, arg):
    #     cdef PyDBAdditionalThreadInfo info;
    #     cdef bint flag;
    # ELSE
    def should_stop_on_exception(self, frame, event, arg):
    # ENDIF

        # main_debugger, _filename, info, _thread = self._args
        main_debugger = self._args[0]
        info = self._args[2]
        flag = False

        if info.pydev_state != STATE_SUSPEND:  #and breakpoint is not None:
            exception, value, trace = arg

            if trace is not None: #on jython trace is None on the first event
                exception_breakpoint = get_exception_breakpoint(
                    exception, main_debugger.break_on_caught_exceptions)

                if exception_breakpoint is not None:
                    if exception_breakpoint.ignore_libraries:
                        if exception_breakpoint.notify_on_first_raise_only:
                            if main_debugger.first_appearance_in_scope(trace):
                                add_exception_to_frame(frame, (exception, value, trace))
                                try:
                                    info.pydev_message = exception_breakpoint.qname
                                except:
                                    info.pydev_message = exception_breakpoint.qname.encode('utf-8')
                                flag = True
                            else:
                                pydev_log.debug("Ignore exception %s in library %s" % (exception, frame.f_code.co_filename))
                                flag = False
                    else:
                        if not exception_breakpoint.notify_on_first_raise_only or just_raised(trace):
                            add_exception_to_frame(frame, (exception, value, trace))
                            try:
                                info.pydev_message = exception_breakpoint.qname
                            except:
                                info.pydev_message = exception_breakpoint.qname.encode('utf-8')
                            flag = True
                        else:
                            flag = False
                else:
                    try:
                        if main_debugger.plugin is not None:
                            result = main_debugger.plugin.exception_break(main_debugger, self, frame, self._args, arg)
                            if result:
                                (flag, frame) = result
                    except:
                        flag = False

        return flag, frame

    def handle_exception(self, frame, event, arg):
        try:
            # print 'handle_exception', frame.f_lineno, frame.f_code.co_name

            # We have 3 things in arg: exception type, description, traceback object
            trace_obj = arg[2]
            main_debugger = self._args[0]

            if not hasattr(trace_obj, 'tb_next'):
                return  #Not always there on Jython...

            initial_trace_obj = trace_obj
            if trace_obj.tb_next is None and trace_obj.tb_frame is frame:
                #I.e.: tb_next should be only None in the context it was thrown (trace_obj.tb_frame is frame is just a double check).

                if main_debugger.break_on_exceptions_thrown_in_same_context:
                    #Option: Don't break if an exception is caught in the same function from which it is thrown
                    return
            else:
                #Get the trace_obj from where the exception was raised...
                while trace_obj.tb_next is not None:
                    trace_obj = trace_obj.tb_next


            if main_debugger.ignore_exceptions_thrown_in_lines_with_ignore_exception:
                for check_trace_obj in (initial_trace_obj, trace_obj):
                    filename = get_abs_path_real_path_and_base_from_frame(check_trace_obj.tb_frame)[1]


                    filename_to_lines_where_exceptions_are_ignored = self.filename_to_lines_where_exceptions_are_ignored


                    lines_ignored = filename_to_lines_where_exceptions_are_ignored.get(filename)
                    if lines_ignored is None:
                        lines_ignored = filename_to_lines_where_exceptions_are_ignored[filename] = {}

                    try:
                        curr_stat = os.stat(filename)
                        curr_stat = (curr_stat.st_size, curr_stat.st_mtime)
                    except:
                        curr_stat = None

                    last_stat = self.filename_to_stat_info.get(filename)
                    if last_stat != curr_stat:
                        self.filename_to_stat_info[filename] = curr_stat
                        lines_ignored.clear()
                        try:
                            linecache.checkcache(filename)
                        except:
                            #Jython 2.1
                            linecache.checkcache()

                    from_user_input = main_debugger.filename_to_lines_where_exceptions_are_ignored.get(filename)
                    if from_user_input:
                        merged = {}
                        merged.update(lines_ignored)
                        #Override what we have with the related entries that the user entered
                        merged.update(from_user_input)
                    else:
                        merged = lines_ignored

                    exc_lineno = check_trace_obj.tb_lineno

                    # print ('lines ignored', lines_ignored)
                    # print ('user input', from_user_input)
                    # print ('merged', merged, 'curr', exc_lineno)

                    if not dict_contains(merged, exc_lineno):  #Note: check on merged but update lines_ignored.
                        try:
                            line = linecache.getline(filename, exc_lineno, check_trace_obj.tb_frame.f_globals)
                        except:
                            #Jython 2.1
                            line = linecache.getline(filename, exc_lineno)

                        if IGNORE_EXCEPTION_TAG.match(line) is not None:
                            lines_ignored[exc_lineno] = 1
                            return
                        else:
                            #Put in the cache saying not to ignore
                            lines_ignored[exc_lineno] = 0
                    else:
                        #Ok, dict has it already cached, so, let's check it...
                        if merged.get(exc_lineno, 0):
                            return


            thread = self._args[3]

            try:
                frame_id_to_frame = {}
                frame_id_to_frame[id(frame)] = frame
                f = trace_obj.tb_frame
                while f is not None:
                    frame_id_to_frame[id(f)] = f
                    f = f.f_back
                f = None

                thread_id = get_thread_id(thread)
                pydevd_vars.add_additional_frame_by_id(thread_id, frame_id_to_frame)
                try:
                    main_debugger.send_caught_exception_stack(thread, arg, id(frame))
                    self.set_suspend(thread, CMD_STEP_CAUGHT_EXCEPTION)
                    self.do_wait_suspend(thread, frame, event, arg)
                    main_debugger.send_caught_exception_stack_proceeded(thread)

                finally:
                    pydevd_vars.remove_additional_frame_by_id(thread_id)
            except:
                traceback.print_exc()

            main_debugger.set_trace_for_frame_and_parents(frame)
        finally:
            #Clear some local variables...
            trace_obj = None
            initial_trace_obj = None
            check_trace_obj = None
            f = None
            frame_id_to_frame = None
            main_debugger = None
            thread = None

    def manage_return_values(self, main_debugger, frame, event, arg):
        try:
            if main_debugger.show_return_values:
                if event == "return" and hasattr(frame, "f_code") and hasattr(frame.f_code, "co_name"):
                    name = frame.f_code.co_name
                    if hasattr(frame, "f_back") and hasattr(frame.f_back, "f_locals"):
                        frame.f_back.f_locals[RETURN_VALUES_PREFIX + name] = arg
            if main_debugger.remove_return_values_flag:
                # Showing return values was turned off, we should remove them from locals dict.
                # The values can be in the current frame or in the back one
                for var_name in dict_keys(frame.f_locals):
                    if var_name.startswith(RETURN_VALUES_PREFIX):
                        dict_pop(frame.f_locals, var_name)
                if hasattr(frame, "f_back") and hasattr(frame.f_back, "f_locals"):
                    for var_name in dict_keys(frame.f_back.f_locals):
                        if var_name.startswith(RETURN_VALUES_PREFIX):
                            dict_pop(frame.f_back.f_locals, var_name)
                main_debugger.remove_return_values_flag = False
        except:
            main_debugger.remove_return_values_flag = False
            traceback.print_exc()

    # IFDEF CYTHON
    # def trace_dispatch(self, frame, str event, arg):
    #     cdef str filename;
    #     cdef bint is_exception_event;
    #     cdef bint has_exception_breakpoints;
    #     cdef bint can_skip;
    #     cdef PyDBAdditionalThreadInfo info;
    #     cdef int step_cmd;
    #     cdef int line;
    #     cdef str curr_func_name;
    #     cdef bint exist_result;
    # ELSE
    def trace_dispatch(self, frame, event, arg):
    # ENDIF

        main_debugger, filename, info, thread = self._args
        try:
            # print 'frame trace_dispatch', frame.f_lineno, frame.f_code.co_name, event
            info.is_tracing = True
            need_trace_return = False

            if main_debugger._finish_debugging_session:
                return None

            if event == 'call' and main_debugger.signature_factory:
                need_trace_return = send_signature_call_trace(main_debugger, frame, filename)
            if event == 'return' and main_debugger.signature_factory:
                send_signature_return_trace(main_debugger, frame, filename, arg)

            plugin_manager = main_debugger.plugin

            is_exception_event = event == 'exception'
            has_exception_breakpoints = main_debugger.break_on_caught_exceptions or main_debugger.has_plugin_exception_breaks

            if is_exception_event:
                if has_exception_breakpoints:
                    flag, frame = self.should_stop_on_exception(frame, event, arg)
                    if flag:
                        self.handle_exception(frame, event, arg)
                        return self.trace_dispatch

            elif event not in ('line', 'call', 'return'):
                #I believe this can only happen in jython on some frontiers on jython and java code, which we don't want to trace.
                return None

            stop_frame = info.pydev_step_stop
            step_cmd = info.pydev_step_cmd

            if is_exception_event:
                breakpoints_for_file = None
                if stop_frame and stop_frame is not frame and step_cmd is CMD_STEP_OVER and \
                                arg[0] in (StopIteration, GeneratorExit) and arg[2] is None:
                    info.pydev_step_cmd = CMD_STEP_INTO
                    info.pydev_step_stop = None
            else:
                # If we are in single step mode and something causes us to exit the current frame, we need to make sure we break
                # eventually.  Force the step mode to step into and the step stop frame to None.
                # I.e.: F6 in the end of a function should stop in the next possible position (instead of forcing the user
                # to make a step in or step over at that location).
                # Note: this is especially troublesome when we're skipping code with the
                # @DontTrace comment.
                if stop_frame is frame and event is 'return' and step_cmd in (CMD_STEP_RETURN, CMD_STEP_OVER):
                    if not frame.f_code.co_flags & CO_GENERATOR:
                        info.pydev_step_cmd = CMD_STEP_INTO
                        info.pydev_step_stop = None

                breakpoints_for_file = main_debugger.breakpoints.get(filename)

                can_skip = False

                if info.pydev_state == STATE_RUN:
                    #we can skip if:
                    #- we have no stop marked
                    #- we should make a step return/step over and we're not in the current frame
                    can_skip = (step_cmd == -1 and stop_frame is None)\
                        or (step_cmd in (CMD_STEP_RETURN, CMD_STEP_OVER) and stop_frame is not frame)

                if can_skip and plugin_manager is not None and main_debugger.has_plugin_line_breaks:
                    can_skip = not plugin_manager.can_not_skip(main_debugger, self, frame)

                if can_skip and main_debugger.show_return_values:
                    # trace function for showing return values after step over
                    if info.pydev_step_cmd == CMD_STEP_OVER and hasattr(frame, "f_back") and frame.f_back == info.pydev_step_stop:
                        can_skip = False

                # Let's check to see if we are in a function that has a breakpoint. If we don't have a breakpoint,
                # we will return nothing for the next trace
                #also, after we hit a breakpoint and go to some other debugging state, we have to force the set trace anyway,
                #so, that's why the additional checks are there.
                if not breakpoints_for_file:
                    if can_skip:
                        if has_exception_breakpoints:
                            return self.trace_exception
                        else:
                            if need_trace_return:
                                return self.trace_return
                            else:
                                return None

                else:
                    #checks the breakpoint to see if there is a context match in some function
                    curr_func_name = frame.f_code.co_name

                    #global context is set with an empty name
                    if curr_func_name in ('?', '<module>'):
                        curr_func_name = ''

                    for breakpoint in dict_iter_values(breakpoints_for_file): #jython does not support itervalues()
                        #will match either global or some function
                        if breakpoint.func_name in ('None', curr_func_name):
                            break

                    else: # if we had some break, it won't get here (so, that's a context that we want to skip)
                        if can_skip:
                            if has_exception_breakpoints:
                                return self.trace_exception
                            else:
                                if need_trace_return:
                                    return self.trace_return
                                else:
                                    return None


            #We may have hit a breakpoint or we are already in step mode. Either way, let's check what we should do in this frame
            #print 'NOT skipped', frame.f_lineno, frame.f_code.co_name, event

            try:
                line = frame.f_lineno
                flag = False
                #return is not taken into account for breakpoint hit because we'd have a double-hit in this case
                #(one for the line and the other for the return).

                stop_info = {}
                breakpoint = None
                exist_result = False
                stop = False
                bp_type = None
                if not flag and event != 'return' and info.pydev_state != STATE_SUSPEND and breakpoints_for_file is not None \
                        and dict_contains(breakpoints_for_file, line):
                    breakpoint = breakpoints_for_file[line]
                    new_frame = frame
                    stop = True
                    if step_cmd == CMD_STEP_OVER and stop_frame is frame and event in ('line', 'return'):
                        stop = False #we don't stop on breakpoint if we have to stop by step-over (it will be processed later)
                elif plugin_manager is not None and main_debugger.has_plugin_line_breaks:
                    result = plugin_manager.get_breakpoint(main_debugger, self, frame, event, self._args)
                    if result:
                        exist_result = True
                        (flag, breakpoint, new_frame, bp_type) = result

                if breakpoint:
                    #ok, hit breakpoint, now, we have to discover if it is a conditional breakpoint
                    # lets do the conditional stuff here
                    if stop or exist_result:
                        condition = breakpoint.condition
                        if condition is not None:
                            try:
                                val = eval(condition, new_frame.f_globals, new_frame.f_locals)
                                if not val:
                                    return self.trace_dispatch

                            except:
                                if type(condition) != type(''):
                                    if hasattr(condition, 'encode'):
                                        condition = condition.encode('utf-8')

                                msg = 'Error while evaluating expression: %s\n' % (condition,)
                                sys.stderr.write(msg)
                                traceback.print_exc()
                                if not main_debugger.suspend_on_breakpoint_exception:
                                    return self.trace_dispatch
                                else:
                                    stop = True
                                    try:
                                        # add exception_type and stacktrace into thread additional info
                                        etype, value, tb = sys.exc_info()
                                        try:
                                            error = ''.join(traceback.format_exception_only(etype, value))
                                            stack = traceback.extract_stack(f=tb.tb_frame.f_back)

                                            # On self.set_suspend(thread, CMD_SET_BREAK) this info will be
                                            # sent to the client.
                                            info.conditional_breakpoint_exception = \
                                                ('Condition:\n' + condition + '\n\nError:\n' + error, stack)
                                        finally:
                                            etype, value, tb = None, None, None
                                    except:
                                        traceback.print_exc()

                        if breakpoint.expression is not None:
                            try:
                                try:
                                    val = eval(breakpoint.expression, new_frame.f_globals, new_frame.f_locals)
                                except:
                                    val = sys.exc_info()[1]
                            finally:
                                if val is not None:
                                    info.pydev_message = str(val)

                        if not main_debugger.first_breakpoint_reached:
                            if event == 'call':
                                if hasattr(frame, 'f_back'):
                                    back = frame.f_back
                                    if back is not None:
                                        # When we start debug session, we call execfile in pydevd run function. It produces an additional
                                        # 'call' event for tracing and we stop on the first line of code twice.
                                        _, back_filename, base = get_abs_path_real_path_and_base_from_frame(back)
                                        if (base == DEBUG_START[0] and back.f_code.co_name == DEBUG_START[1]) or \
                                                (base == DEBUG_START_PY3K[0] and back.f_code.co_name == DEBUG_START_PY3K[1]):
                                            stop = False
                                            main_debugger.first_breakpoint_reached = True
                else:
                    # if the frame is traced after breakpoint stop,
                    # but the file should be ignored while stepping because of filters
                    if step_cmd != -1:
                        if main_debugger.is_filter_enabled and main_debugger.is_ignored_by_filters(filename):
                            # ignore files matching stepping filters
                            return self.trace_dispatch
                        if main_debugger.is_filter_libraries and main_debugger.not_in_scope(filename):
                            # ignore library files while stepping
                            return self.trace_dispatch

                if main_debugger.show_return_values or main_debugger.remove_return_values_flag:
                    self.manage_return_values(main_debugger, frame, event, arg)

                if stop:
                    self.set_suspend(thread, CMD_SET_BREAK)
                elif flag and plugin_manager is not None:
                    result = plugin_manager.suspend(main_debugger, thread, frame, bp_type)
                    if result:
                        frame = result

                # if thread has a suspend flag, we suspend with a busy wait
                if info.pydev_state == STATE_SUSPEND:
                    self.do_wait_suspend(thread, frame, event, arg)
                    return self.trace_dispatch

            except:
                traceback.print_exc()
                raise

            #step handling. We stop when we hit the right frame
            try:
                should_skip = 0
                if pydevd_dont_trace.should_trace_hook is not None:
                    if self.should_skip == -1:
                        # I.e.: cache the result on self.should_skip (no need to evaluate the same frame multiple times).
                        # Note that on a code reload, we won't re-evaluate this because in practice, the frame.f_code
                        # Which will be handled by this frame is read-only, so, we can cache it safely.
                        if not pydevd_dont_trace.should_trace_hook(frame, filename):
                            # -1, 0, 1 to be Cython-friendly
                            should_skip = self.should_skip = 1
                        else:
                            should_skip = self.should_skip = 0
                    else:
                        should_skip = self.should_skip

                plugin_stop = False
                if should_skip:
                    stop = False

                elif step_cmd == CMD_STEP_INTO:
                    stop = event in ('line', 'return')
                    if plugin_manager is not None:
                        result = plugin_manager.cmd_step_into(main_debugger, frame, event, self._args, stop_info, stop)
                        if result:
                            stop, plugin_stop = result

                elif step_cmd == CMD_STEP_INTO_MY_CODE:
                    if not main_debugger.not_in_scope(frame.f_code.co_filename):
                        stop = event == 'line'

                elif step_cmd == CMD_STEP_OVER:
                    stop = stop_frame is frame and event in ('line', 'return')

                    if frame.f_code.co_flags & CO_GENERATOR:
                        if event is 'return':
                            stop = False

                    if plugin_manager is not None:
                        result = plugin_manager.cmd_step_over(main_debugger, frame, event, self._args, stop_info, stop)
                        if result:
                            stop, plugin_stop = result

                elif step_cmd == CMD_SMART_STEP_INTO:
                    stop = False
                    if info.pydev_smart_step_stop is frame:
                        info.pydev_func_name = '.invalid.' # Must match the type in cython
                        info.pydev_smart_step_stop = None

                    if event == 'line' or event == 'exception':
                        curr_func_name = frame.f_code.co_name

                        #global context is set with an empty name
                        if curr_func_name in ('?', '<module>') or curr_func_name is None:
                            curr_func_name = ''

                        if curr_func_name == info.pydev_func_name:
                            stop = True

                elif step_cmd == CMD_STEP_RETURN:
                    stop = event == 'return' and stop_frame is frame

                elif step_cmd == CMD_RUN_TO_LINE or step_cmd == CMD_SET_NEXT_STATEMENT:
                    stop = False

                    if event == 'line' or event == 'exception':
                        #Yes, we can only act on line events (weird hum?)
                        #Note: This code is duplicated at pydevd.py
                        #Acting on exception events after debugger breaks with exception
                        curr_func_name = frame.f_code.co_name

                        #global context is set with an empty name
                        if curr_func_name in ('?', '<module>'):
                            curr_func_name = ''

                        if curr_func_name == info.pydev_func_name:
                            line = info.pydev_next_line
                            if frame.f_lineno == line:
                                stop = True
                            else:
                                if frame.f_trace is None:
                                    frame.f_trace = self.trace_dispatch
                                frame.f_lineno = line
                                frame.f_trace = None
                                stop = True

                else:
                    stop = False

                if stop and step_cmd != -1 and IS_PY3K:
                    # in Py3k we start script via our custom `execfile` function, and we shouldn't stop there
                    # while stepping when execution is finished
                    if event == 'return' and hasattr(frame, "f_back") and hasattr(frame.f_back, "f_code"):
                        back_filename = os.path.basename(frame.f_back.f_code.co_filename)
                        file_type = get_file_type(back_filename)
                        if file_type == PYDEV_FILE:
                            stop = False

                if plugin_stop:
                    stopped_on_plugin = plugin_manager.stop(main_debugger, frame, event, self._args, stop_info, arg, step_cmd)
                elif stop:
                    if event == 'line':
                        self.set_suspend(thread, step_cmd)
                        self.do_wait_suspend(thread, frame, event, arg)
                    else: #return event
                        back = frame.f_back
                        if back is not None:
                            #When we get to the pydevd run function, the debugging has actually finished for the main thread
                            #(note that it can still go on for other threads, but for this one, we just make it finish)
                            #So, just setting it to None should be OK
                            _, back_filename, base = get_abs_path_real_path_and_base_from_frame(back)
                            if base == DEBUG_START[0] and back.f_code.co_name == DEBUG_START[1]:
                                back = None

                            elif base == TRACE_PROPERTY:
                                # We dont want to trace the return event of pydevd_traceproperty (custom property for debugging)
                                #if we're in a return, we want it to appear to the user in the previous frame!
                                return None

                            elif pydevd_dont_trace.should_trace_hook is not None:
                                if not pydevd_dont_trace.should_trace_hook(back, back_filename):
                                    # In this case, we'll have to skip the previous one because it shouldn't be traced.
                                    # Also, we have to reset the tracing, because if the parent's parent (or some
                                    # other parent) has to be traced and it's not currently, we wouldn't stop where
                                    # we should anymore (so, a step in/over/return may not stop anywhere if no parent is traced).
                                    # Related test: _debugger_case17a.py
                                    main_debugger.set_trace_for_frame_and_parents(back, overwrite_prev_trace=True)
                                    return None

                        if back is not None:
                            #if we're in a return, we want it to appear to the user in the previous frame!
                            self.set_suspend(thread, step_cmd)
                            self.do_wait_suspend(thread, back, event, arg)
                        else:
                            #in jython we may not have a back frame
                            info.pydev_step_stop = None
                            info.pydev_step_cmd = -1
                            info.pydev_state = STATE_RUN

            except KeyboardInterrupt:
                raise
            except:
                try:
                    traceback.print_exc()
                    info.pydev_step_cmd = -1
                except:
                    return None

            #if we are quitting, let's stop the tracing
            retVal = None
            if not main_debugger.quitting:
                retVal = self.trace_dispatch

            return retVal
        finally:
            info.is_tracing = False

        #end trace_dispatch

