import unittest
from config import config
from ok.test.TaskTestCase import TaskTestCase
from src.task.TacetTask import TacetTask

config['debug'] = True


class TestTacet(TaskTestCase):
    task_class = TacetTask
    config = config

    def test_find_treasure_icon(self):
        self.set_image('tests/images/treasure.png')
        treasure = self.task.find_treasure_icon()
        self.logger.info(f'find_treasure_icon1 {treasure}')
        self.assertIsNotNone(treasure)

        self.set_image('tests/images/treasure2.png')
        treasure = self.task.find_treasure_icon()
        self.logger.info(f'find_treasure_icon2 {treasure}')
        self.assertIsNotNone(treasure)


class TestTacetClaimLimit(unittest.TestCase):

    def test_exits_after_reaching_claim_limit_instead_of_continuing_challenge(self):
        task = TacetTask.__new__(TacetTask)
        task.config = {'Which Tacet Suppression to Farm': 1}
        task.stamina_once = 60
        task.info_incr = lambda *args, **kwargs: None
        task.log_info = lambda *args, **kwargs: None
        task.sleep = lambda *args, **kwargs: None
        task.openF2Book = lambda *args, **kwargs: None
        task.get_stamina = lambda: (240, 0, 240)
        task.open_boss_book = lambda *args, **kwargs: None
        task.teleport_to_tacet = lambda *args, **kwargs: None
        task.click_team_challenge = lambda *args, **kwargs: None
        task.wait_in_team_and_world = lambda *args, **kwargs: True
        task.combat_once = lambda *args, **kwargs: None
        task.walk_to_treasure = lambda *args, **kwargs: None
        task.pick_f = lambda *args, **kwargs: None
        task.has_claim_stamina = lambda: True
        task.use_stamina = lambda *args, **kwargs: (True, 120)

        clicks = []
        task.click = lambda x, y, **kwargs: clicks.append((x, y, kwargs))

        used = task.farm_tacet(max_claims=2)

        self.assertEqual(120, used)
        self.assertEqual(0.365, clicks[-1][0])
        self.assertEqual(0.853, clicks[-1][1])
        self.assertNotIn((0.640, 0.851), [(x, y) for x, y, _ in clicks])

if __name__ == '__main__':
    unittest.main()
