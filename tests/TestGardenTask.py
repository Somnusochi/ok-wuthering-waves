import unittest

from src.task.GardenTask import GardenTask


class TestGardenTask(unittest.TestCase):

    def test_claim_weekly_reward_skips_check_when_already_confirmed(self):
        task = GardenTask.__new__(GardenTask)
        calls = []

        task.info_set = lambda *args, **kwargs: calls.append(('info_set', args, kwargs))
        task.open_garden_weekly_tab = lambda: calls.append(('open_garden_weekly_tab', (), {}))
        task.is_weekly_garden_completed = lambda: calls.append(('is_weekly_garden_completed', (), {})) or True
        task.log_info = lambda *args, **kwargs: calls.append(('log_info', args, kwargs))
        task.click_garden_weekly_action = lambda: calls.append(('click_garden_weekly_action', (), {}))
        task.ensure_main = lambda *args, **kwargs: calls.append(('ensure_main', args, kwargs))

        self.assertTrue(task.claim_weekly_garden_reward(already_confirmed=True))

        call_names = [call[0] for call in calls]
        self.assertNotIn('open_garden_weekly_tab', call_names)
        self.assertNotIn('is_weekly_garden_completed', call_names)
        self.assertIn('click_garden_weekly_action', call_names)
        self.assertIn('ensure_main', call_names)


if __name__ == '__main__':
    unittest.main()
