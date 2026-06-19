import unittest

from src.task.AutoCombatTask import AutoCombatTask
from src.util.ControllerTrigger import ControllerTrigger, XINPUT_GAMEPAD_RIGHT_THUMB


class TestControllerTrigger(unittest.TestCase):

    def test_r3_triggers_only_on_new_press(self):
        states = [0, XINPUT_GAMEPAD_RIGHT_THUMB, XINPUT_GAMEPAD_RIGHT_THUMB, 0, XINPUT_GAMEPAD_RIGHT_THUMB]
        trigger = ControllerTrigger(state_reader=lambda: states.pop(0))

        self.assertFalse(trigger.consume_pressed("R3"))
        self.assertTrue(trigger.consume_pressed("R3"))
        self.assertFalse(trigger.consume_pressed("R3"))
        self.assertFalse(trigger.consume_pressed("R3"))
        self.assertTrue(trigger.consume_pressed("R3"))

    def test_disabled_controller_trigger_does_not_read_state(self):
        reads = []
        trigger = ControllerTrigger(state_reader=lambda: reads.append(True) or XINPUT_GAMEPAD_RIGHT_THUMB)

        self.assertFalse(trigger.consume_pressed("Disabled"))
        self.assertEqual([], reads)

    def test_auto_combat_controller_trigger_bridges_to_existing_combat_flow(self):
        task = AutoCombatTask.__new__(AutoCombatTask)
        task.config = {
            "Controller Trigger": "R3",
            "Use Liberation": True,
        }
        task.scene = type("Scene", (), {
            "in_team": lambda self, checker: True,
        })()
        task.in_team_and_world = lambda: True
        task.in_world = lambda: True
        task.warm_up_char_features = lambda: None
        task.controller_trigger = type("Trigger", (), {
            "consume_pressed": lambda self, name: True,
        })()
        task.clicks = []
        task.click = lambda after_sleep=0: task.clicks.append(after_sleep)
        task.log_info = lambda *args, **kwargs: None

        combat_checks = [False, True, False]
        task.in_combat = lambda: combat_checks.pop(0)
        performed = []
        task.get_current_char = lambda: type("Char", (), {
            "perform": lambda self: performed.append(True),
        })()
        task.combat_end = lambda: performed.append("end")

        self.assertTrue(task.run())
        self.assertEqual([0.05], task.clicks)
        self.assertEqual([True, "end"], performed)

if __name__ == "__main__":
    unittest.main()
