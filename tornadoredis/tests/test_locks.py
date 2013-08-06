from tornado.gen import engine, Task
from .redistest import RedisTestCase, async_test


class LocksTestCase(RedisTestCase):

    @async_test
    @engine
    def test_locks(self):

        '''
        The idea of this test is simple:
        1. Acquire a lock using a Lock object.
        2. See that trying to acquire it with a different Lock object fails, if blocking=False.
        3. Try to acquire it, with blocking=True. Release it in the first Lock to see that the acquiring succeeds.
        '''

        print "Trying to get the lock"
        my_lock = self.client.lock("testLock", lock_ttl=10, polling_interval=0.1)
        print "Acquiring..."
        result = yield Task(my_lock.acquire, blocking=True)
        print "Result: %s (should be True)" % result
        self.assertEqual(result, True)

        print "Trying to get the lock again with a different Lock"
        my_lock2 = self.client.lock("testLock", lock_ttl=10, polling_interval=0.1)
        print "Acquiring..."
        result = yield Task(my_lock2.acquire, blocking=False)
        print "Result: %s (should be False)" % result
        self.assertEqual(result, False)

        print "Trying to acquire and release at the same time..."
        self.io_loop.add_timeout(self.io_loop.time() + 1, my_lock.release)
        result = yield Task(my_lock2.acquire, blocking=True)
        print "Result: %s (should be True)" % result
        self.assertEqual(result, True)

        yield Task(my_lock2.release)
        print "Released!"

        self.stop()