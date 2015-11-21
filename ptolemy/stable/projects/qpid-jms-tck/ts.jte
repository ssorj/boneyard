#
# Copyright 2002 Sun Microsystems, Inc. All rights reserved.
# SUN PROPRIETARY/CONFIDENTIAL. Use is subject to license terms.
#

#
# @(#)ts.jte	1.1 02/05/08
#
#########################################################################
#                                                                   	#
#   JavaTest Environment file for JMS Compatibility Test Suite          #
#                                                                       #
#   Environment specific properties in this file will likely	 	    #
#   have to be modified prior to running the JMS TCK. Instructions	    #
#   for modifying these properties are contained in this file.	 	    #
#                                                                       #
#########################################################################

# Command Macros
ExecJCKTestSameJVMCmd=com.sun.javatest.lib.ExecJCKTestSameJVMCmd
ExecJCKTestOtherJVMCmd=com.sun.javatest.lib.ExecJCKTestOtherJVMCmd

 
########################################################################
# Environment ts_unix                                              #
########################################################################

env.ts_unix.description=\
        Run the runtime tests in a separate JVM (process) on Solaris
env.ts_unix.menu=true
env.ts_unix.testsuite=com.sun.ts.lib.harness.TS
env.ts_unix.command.testExecute=com.sun.ts.lib.harness.ExecTSTestCmd \
    CLASSPATH=${TS_HOME}/lib/jmstck.jar:${TS_HOME}/lib/tsharness.jar:${TS_HOME}/lib/apiCheck.jar:${TS_HOME}/lib/javatest.jar:${TS_HOME}/classes:${JAVA_HOME}/lib/rt.jar:${LOCAL_CLASSES} \
    ${JAVA_HOME}/bin/java \
    -Ddeliverable.class="${deliverable.class}" \
    -Dlog4j.configuration="${log4j.configuration}" \
    ${JAVA_OPTIONS} $testExecuteClass $testExecuteArgs

#    -Djava.naming.factory.initial=org.apache.qpid.jndi.PropertiesFileInitialContextFactory \

########################################################################
# Environment ts_win32						       #
########################################################################
env.ts_win32.description=\
        Run the runtime tests in a separate JVM (process) on Win32
env.ts_win32.menu=true
env.ts_win32.testsuite=com.sun.ts.lib.harness.TS
env.ts_win32.command.testExecute=com.sun.ts.lib.harness.ExecTSTestCmd \
        CLASSPATH=${TS_HOME}\\lib\\jmstck.jar;${TS_HOME}\\lib\\tsharness.jar;$TS_HOME\\lib\\apiCheck.jar;${TS_HOME}\\lib\\javatest.jar;${TS_HOME}\\classes;${JAVA_HOME}\\jre\\lib\\rt.jar;${LOCAL_CLASSES} \
	windir=${windir} \
	SYSTEMROOT=${SYSTEMROOT} \
        ${JAVA_HOME}\\bin\\java \
		-Ddeliverable.class=${deliverable.class} ${JAVA_OPTIONS} $testExecuteClass $testExecuteArgs

########################################################################
#These properties are used by the Javatest harness. "harness.log.port"
#specifies the port that server components use to send logging
#output back to JavaTest.  If the default port # is not available
#on the machine running JavaTest, then you can set it here. 
#
#"harness.log.traceflag" is used to turn on/off verbose debugging output
#for the tests.
#
########################################################################
harness.temp.directory=${TS_HOME}
harness.log.port=2001
harness.log.traceflag=true
harness.log.mode=silent
harness.log.delayseconds=1 
deliverable.class=com.sun.ts.lib.deliverable.jms.JMSDeliverable
ts_home=${TS_HOME}

########################################################################
# This property is used by porting class to set JNDI name
########################################################################
porting.ts.jmsObjects.class.1=com.sun.ts.lib.implementation.sun.jms.SunRIJMSObjects

###############################################################
#These properties are needed for the JMS tests.
###############################################################
jms_timeout=5000
user=guest
password=guest
