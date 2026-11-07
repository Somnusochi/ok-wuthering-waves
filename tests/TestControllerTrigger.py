import unittest
from unittest.mock import Mock, patch

from src.task.AutoCombatTask import AutoCombatTask
from src.task.BaseCombatTask import BaseCombatTask
from src.scene.WWScene import WWScene
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

    def test_auto_combat_treats_single_member_combat_hud_as_team(self):
        class ProbeAutoCombatTask(AutoCombatTask):
            @property
            def logged_in(self):
                return getattr(self, "_logged_in", False)

            @logged_in.setter
            def logged_in(self, value):
                self._logged_in = value

        task = ProbeAutoCombatTask.__new__(ProbeAutoCombatTask)
        task.find_one = lambda name, **kwargs: None
        task.has_target = lambda: True
        task.has_health_bar = lambda: True

        self.assertEqual((True, 0, 1), task.in_team())
        self.assertTrue(task.logged_in)

    def test_auto_combat_does_not_treat_empty_screen_as_single_member_team(self):
        task = AutoCombatTask.__new__(AutoCombatTask)
        task.find_one = lambda name, **kwargs: None
        task.has_target = lambda: False
        task.has_health_bar = lambda: False

        self.assertEqual((False, -1, 1), task.in_team())

    def test_single_member_fallback_requires_target_and_enemy_health(self):
        for target, health in ((False, False), (False, True), (True, False)):
            with self.subTest(target=target, health=health):
                task = AutoCombatTask.__new__(AutoCombatTask)
                task.find_one = lambda name, **kwargs: object() if name == 'world_earth_icon' else None
                task.has_target = lambda: target
                task.has_health_bar = lambda: health

                self.assertEqual((False, -1, 1), task.in_team())

    def test_single_member_fallback_preserves_upstream_abyss_and_animation_checks(self):
        for field in ('_abyss_combat_active', '_in_liberation'):
            with self.subTest(field=field):
                task = AutoCombatTask.__new__(AutoCombatTask)
                setattr(task, field, True)
                task.find_one = lambda *args, **kwargs: None
                task.single_member_team_hud_visible = Mock(return_value=True)

                self.assertEqual((False, -1, 1), task.in_team())
                task.single_member_team_hud_visible.assert_not_called()

    def test_known_normal_party_does_not_become_single_member_when_hud_disappears(self):
        for size in (2, 3):
            with self.subTest(size=size):
                task = AutoCombatTask.__new__(AutoCombatTask)
                with patch('src.task.BaseWWTask.BaseWWTask.in_team', return_value=(True, 1, size)):
                    self.assertEqual((True, 1, size), task.in_team())
                task.find_one = lambda *args, **kwargs: None
                task.single_member_team_hud_visible = Mock(return_value=True)

                self.assertEqual((False, -1, 1), task.in_team())
                task.single_member_team_hud_visible.assert_not_called()

    def test_combat_reset_allows_a_later_single_member_story_encounter(self):
        task = AutoCombatTask.__new__(AutoCombatTask)
        task._normal_party_size = 3
        task.reset_to_false = Mock(return_value=False)

        task.reset_auto_combat('left normal party')

        self.assertEqual(0, task._normal_party_size)
        self.assertEqual([None, None, None], task.chars)
        task.reset_to_false.assert_called_once_with('left normal party')

    def test_abyss_settlement_does_not_keep_timer_guard_alive_without_party_hud(self):
        task = AutoCombatTask.__new__(AutoCombatTask)
        task._abyss_force_combat_until = 0
        task._abyss_combat_active = True
        task.get_abyss_remaining_time = Mock(return_value=5.0)
        task.scene = WWScene()
        task._in_combat = True
        task.in_liberation = False
        task.find_one = lambda *args, **kwargs: None
        task.single_member_team_hud_visible = Mock(return_value=True)
        task.check_f_break = Mock()
        task.get_current_char = Mock(return_value=None)
        task.on_combat_check = Mock(return_value=True)
        task.has_target = Mock(return_value=False)
        task.combat_end_condition = None
        task.check_health_bar = Mock(return_value=False)
        task.target_enemy_time_out = 3
        task.target_enemy = Mock(return_value=False)
        task.should_check_monthly_card = Mock(return_value=False)
        task.reset_to_false = Mock(return_value=False)

        self.assertFalse(BaseCombatTask.do_check_in_combat(task, False))

        task.get_abyss_remaining_time.assert_not_called()
        task.single_member_team_hud_visible.assert_not_called()
        task.reset_to_false.assert_called_once_with(reason='target enemy failed')


if __name__ == "__main__":
    unittest.main()
