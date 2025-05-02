/*
 * Copyright The async-profiler authors
 * SPDX-License-Identifier: Apache-2.0
 */

package test.lock;

import one.profiler.test.Assert;
import one.profiler.test.Output;
import one.profiler.test.Test;
import one.profiler.test.TestProcess;

public class LockTests {

    @Test(mainClass = DatagramTest.class, debugNonSafepoints = true)
    public void datagramSocketLock(TestProcess p) throws Exception {
        Output out = p.profile("-e cpu -d 3 -o collapsed --cstack dwarf");
        System.err.println(out);
        System.err.println("----");
        System.err.println(out.ratio("(PlatformEvent::.ark|PlatformEvent::.npark)"));
        System.err.println(out.ratio("ReentrantLock.lock"));
        System.err.println(out.ratio("ReentrantLock.unlock"));

        assert out.ratio("(PlatformEvent::.ark|PlatformEvent::.npark)") > 0.1
                || ((out.ratio("ReentrantLock.lock") + out.ratio("ReentrantLock.unlock")) > 0.1 && out.contains("Unsafe_.ark"));
        out = p.profile("-e lock -d 3 -o collapsed");
        System.err.println(out);
        assert out.contains("sun/nio/ch/DatagramChannelImpl.send");
    }
}
