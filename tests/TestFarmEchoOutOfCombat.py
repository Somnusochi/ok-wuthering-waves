import unittest
from unittest.mock import patch

from src.task.BaseCombatTask import CharDeadException, CharRevivedException, NotInCombatException
from src.task.FarmEchoTask import FarmEchoTask
from src.task.WWOneTimeTask import WWOneTimeTask

OUT_OF_COMBAT = 'sleep check not in combat'


def raiser(exception):
    def _raise(*args, **kwargs):
        raise exception

    return _raise


class TestFarmEchoOutOfCombatSurvival(unittest.TestCase):
    """掉锁定导致的脱战只应该废掉一轮, 不应该终止整个刷取任务。"""

    def make_task(self, repeat=2):
        task = FarmEchoTask.__new__(FarmEchoTask)
        task.config = {'Repeat Farm Count': repeat, 'Use Liberation': False}
        task.combat_wait_time = 3
        task.bypass_end_wait = True
        task._just_entered_boss_realm = False
        task.logs = []
        task.order = []
        task.combat_once = lambda *args, **kwargs: True
        noop = lambda *args, **kwargs: None
        for name in ('manage_boss_parameters', 'log_debug', 'log_error', 'init_parameters', 'in_realm_check',
                     'manage_boss_interactions', 'check_boss_name', 'incr_drop'):
            setattr(task, name, noop)
        task.do_reset_to_false = lambda: task.order.append('reset')
        task.in_realm = lambda: True
        task.in_combat = lambda *args, **kwargs: True
        task.pick_echo = lambda: True
        task.teleport_to_boss_enabled = lambda: False
        task.log_info = lambda message, **kwargs: task.logs.append(message)
        return task

    def test_combat_wait_survives_target_lock_flicker(self):
        task = self.make_task(repeat=2)
        sleeps = []

        def sleep(timeout):
            sleeps.append(timeout)
            if len(sleeps) == 1:
                raise NotInCombatException(OUT_OF_COMBAT)

        task.sleep = sleep

        task.do_run()

        self.assertEqual(2, len(sleeps))  # 第一轮脱战后仍然跑完了第二轮
        self.assertIn(f'out of combat during combat wait, ignored: {OUT_OF_COMBAT}', task.logs)

    def test_combat_wait_still_propagates_char_death(self):
        task = self.make_task(repeat=2)
        task.sleep = raiser(CharDeadException('char dead'))

        with self.assertRaises(CharDeadException):
            task.do_run()

    def test_combat_wait_still_propagates_revive(self):
        task = self.make_task(repeat=2)
        task.teleport_to_boss_enabled = lambda: True
        task.teleport_to_configured_boss_and_prepare = lambda: task.order.append('teleport')
        task.sleep = raiser(CharRevivedException('char revived'))

        task.do_run()

        self.assertIn('teleport', task.order)  # 死亡复苏仍然走重新传送流程
        self.assertIn('farm 4c: death recovered, teleport to boss again', task.logs)

    def test_start_resets_stale_combat_state_before_sleeping(self):
        task = self.make_task(repeat=1)
        task.sleep = lambda timeout: None

        def stale_start(_self):
            task.order.append('start')
            raise NotInCombatException(OUT_OF_COMBAT)

        with patch.object(WWOneTimeTask, 'run', stale_start):
            task.run()

        self.assertEqual(['reset', 'start'], task.order)  # 必须先清残留再启动
        self.assertIn(f'out of combat while starting, ignored: {OUT_OF_COMBAT}', task.logs)

    def test_start_still_propagates_char_death(self):
        task = self.make_task(repeat=1)
        task.sleep = lambda timeout: None

        def dead_start(_self):
            raise CharDeadException('char dead')

        with patch.object(WWOneTimeTask, 'run', dead_start):
            with self.assertRaises(CharDeadException):
                task.run()


if __name__ == '__main__':
    unittest.main()
