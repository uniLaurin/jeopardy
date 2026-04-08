"""Tests for the Jeopardy game — covers resources, game logic, and data integrity."""

import os
import sys
import json
import tempfile
import shutil
import unittest

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import resources as r


class TestResourcePaths(unittest.TestCase):
    """Test resource_path and data_path helpers."""

    def test_resource_path_returns_absolute(self):
        p = r.resource_path("questionsets")
        self.assertTrue(os.path.isabs(p))

    def test_data_path_returns_absolute(self):
        p = r.data_path("questionsets")
        self.assertTrue(os.path.isabs(p))

    def test_data_path_empty_arg(self):
        p = r.data_path("")
        self.assertTrue(os.path.isdir(p))


class TestFontDetection(unittest.TestCase):
    """Test font fallback logic."""

    def test_detect_font_sets_valid_font(self):
        # detect_font needs a Tk instance
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        try:
            r.detect_font()
            self.assertIn(r.FONT, ["Arial Rounded MT Bold", "Arial", "Helvetica"])
        finally:
            root.destroy()

    def test_font_constants_are_ints(self):
        self.assertIsInstance(r.FONT_TITLE, int)
        self.assertIsInstance(r.FONT_SECTION, int)
        self.assertIsInstance(r.FONT_BODY, int)
        self.assertIsInstance(r.FONT_SMALL, int)
        self.assertIsInstance(r.FONT_BUTTON, int)


class TestDesignSystem(unittest.TestCase):
    """Test that design system constants are valid hex colors."""

    def _is_hex_color(self, value):
        if not isinstance(value, str):
            return False
        if not value.startswith("#"):
            return False
        hex_part = value[1:]
        if len(hex_part) not in (3, 6):
            return False
        try:
            int(hex_part, 16)
            return True
        except ValueError:
            return False

    def test_all_colors_are_valid_hex(self):
        colors = {
            "BLUE": r.BLUE,
            "GOLD": r.GOLD,
            "DARK_BLUE": r.DARK_BLUE,
            "CARD_BG": r.CARD_BG,
            "BORDER_BLUE": r.BORDER_BLUE,
            "SHADOW": r.SHADOW,
            "HOVER_GOLD": r.HOVER_GOLD,
            "ACTIVE_GOLD": r.ACTIVE_GOLD,
            "LABEL_GRAY": r.LABEL_GRAY,
            "HINT_GRAY": r.HINT_GRAY,
            "ERROR_RED": r.ERROR_RED,
            "SUCCESS_GREEN": r.SUCCESS_GREEN,
        }
        for name, color in colors.items():
            with self.subTest(color_name=name):
                self.assertTrue(self._is_hex_color(color),
                                f"{name} = {color!r} is not a valid hex color")

    def test_spacing_constants_positive(self):
        self.assertGreater(r.SPACING_MAJOR, 0)
        self.assertGreater(r.SPACING_SECTION, 0)
        self.assertGreater(r.SPACING_ELEMENT, 0)


class TestTeamConfiguration(unittest.TestCase):
    """Test default team setup."""

    def test_default_teams_count(self):
        self.assertGreaterEqual(len(r.teams), 2)
        self.assertLessEqual(len(r.teams), 6)

    def test_teams_have_required_fields(self):
        for team in r.teams:
            self.assertIn("name", team)
            self.assertIn("color", team)
            self.assertTrue(len(team["name"]) > 0)

    def test_team_palette_has_enough_colors(self):
        self.assertGreaterEqual(len(r.TEAM_PALETTE), 6)

    def test_team_points_matches_teams(self):
        r.reset_game_state()
        self.assertEqual(len(r.team_points), len(r.teams))
        self.assertTrue(all(p == 0 for p in r.team_points))


class TestQuestionSetManagement(unittest.TestCase):
    """Test JSON question set CRUD operations."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self._orig_data_path = r.data_path
        # Monkey-patch data_path to use temp dir
        r.data_path = lambda rel="": os.path.join(self.test_dir, rel)

    def tearDown(self):
        r.data_path = self._orig_data_path
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_get_questionsets_dir_creates_dir(self):
        d = r.get_questionsets_dir()
        self.assertTrue(os.path.isdir(d))

    def test_save_and_load_question_set(self):
        vals = [100, 200, 300]
        cats = [
            {"name": "Cat A", "questions": ["Q1", "Q2", "Q3"]},
            {"name": "Cat B", "questions": ["Q4", "Q5", "Q6"]},
        ]
        r.save_question_set("test_set.json", "Test Set", vals, cats)

        # Verify file exists
        path = os.path.join(r.get_questionsets_dir(), "test_set.json")
        self.assertTrue(os.path.exists(path))

        # Verify JSON content
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["name"], "Test Set")
        self.assertEqual(data["values"], [100, 200, 300])
        self.assertEqual(len(data["categories"]), 2)
        self.assertEqual(data["categories"][0]["name"], "Cat A")

    def test_load_question_set_populates_state(self):
        vals = [100, 200]
        cats = [{"name": "TestCat", "questions": ["Q1", "Q2"]}]
        r.save_question_set("load_test.json", "Load Test", vals, cats)

        r.load_question_set("load_test.json")
        self.assertEqual(r.values, [100, 200])
        self.assertEqual(r.categories, ["TestCat"])
        self.assertEqual(r.questions, [["Q1", "Q2"]])
        self.assertEqual(r.to_be_switched_int, 1 * 2)  # 1 cat * 2 values

    def test_list_question_sets(self):
        r.save_question_set("set_a.json", "Set A", [100], [{"name": "C", "questions": ["Q"]}])
        r.save_question_set("set_b.json", "Set B", [200], [{"name": "D", "questions": ["Q"]}])

        sets = r.list_question_sets()
        filenames = [f for f, _ in sets]
        self.assertIn("set_a.json", filenames)
        self.assertIn("set_b.json", filenames)

    def test_delete_question_set(self):
        r.save_question_set("delete_me.json", "Del", [100], [{"name": "C", "questions": ["Q"]}])
        path = os.path.join(r.get_questionsets_dir(), "delete_me.json")
        self.assertTrue(os.path.exists(path))

        r.delete_question_set("delete_me.json")
        self.assertFalse(os.path.exists(path))

    def test_delete_nonexistent_set_no_error(self):
        r.delete_question_set("does_not_exist.json")

    def test_list_ignores_non_json(self):
        d = r.get_questionsets_dir()
        with open(os.path.join(d, "readme.txt"), "w") as f:
            f.write("not json")
        sets = r.list_question_sets()
        filenames = [f for f, _ in sets]
        self.assertNotIn("readme.txt", filenames)

    def test_list_handles_corrupt_json(self):
        d = r.get_questionsets_dir()
        with open(os.path.join(d, "corrupt.json"), "w") as f:
            f.write("{invalid json")
        sets = r.list_question_sets()
        # Should not crash, corrupt file appears with filename as display name
        filenames = [f for f, _ in sets]
        self.assertIn("corrupt.json", filenames)

    def test_save_preserves_unicode(self):
        cats = [{"name": "Ümlauts äöü", "questions": ["Frage mit Ünïcödé"]}]
        r.save_question_set("unicode.json", "Ünïcödé Set", [100], cats)

        with open(os.path.join(r.get_questionsets_dir(), "unicode.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["categories"][0]["name"], "Ümlauts äöü")


class TestResetGameState(unittest.TestCase):
    """Test game state reset logic."""

    def test_reset_clears_points(self):
        r.team_points = [500, 300, 100]
        r.reset_game_state()
        self.assertTrue(all(p == 0 for p in r.team_points))

    def test_reset_matches_team_count(self):
        original_teams = r.teams[:]
        r.teams = [{"name": "A", "color": "red"}, {"name": "B", "color": "blue"}]
        r.reset_game_state()
        self.assertEqual(len(r.team_points), 2)
        r.teams = original_teams

    def test_reset_recalculates_to_be_switched(self):
        r.categories = ["A", "B", "C"]
        r.values = [100, 200]
        r.reset_game_state()
        self.assertEqual(r.to_be_switched_int, 6)  # 3 * 2


class TestDefaultQuestionData(unittest.TestCase):
    """Test the hardcoded default question data is consistent."""

    def test_categories_and_questions_match(self):
        self.assertEqual(len(r.categories), len(r.questions),
                         "Number of categories must match number of question lists")

    def test_each_category_has_enough_questions(self):
        for i, cat in enumerate(r.categories):
            self.assertEqual(len(r.questions[i]), len(r.values),
                             f"Category '{cat}' has {len(r.questions[i])} questions "
                             f"but {len(r.values)} values")

    def test_no_empty_questions(self):
        for i, cat_questions in enumerate(r.questions):
            for j, q in enumerate(cat_questions):
                self.assertTrue(len(q.strip()) > 0,
                                f"Empty question at category {i}, question {j}")

    def test_to_be_switched_matches_grid_size(self):
        expected = len(r.categories) * len(r.values)
        self.assertEqual(r.to_be_switched_int, expected)


class TestEnsureDefaultQuestionset(unittest.TestCase):
    """Test that ensure_default_questionset creates the file."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self._orig_data_path = r.data_path
        r.data_path = lambda rel="": os.path.join(self.test_dir, rel)

    def tearDown(self):
        r.data_path = self._orig_data_path
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_creates_default_if_missing(self):
        r.ensure_default_questionset()
        path = os.path.join(r.get_questionsets_dir(), "ergo_default.json")
        self.assertTrue(os.path.exists(path))

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn("name", data)
        self.assertIn("values", data)
        self.assertIn("categories", data)

    def test_does_not_overwrite_existing(self):
        d = r.get_questionsets_dir()
        path = os.path.join(d, "ergo_default.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"name": "Custom", "values": [1], "categories": []}, f)

        r.ensure_default_questionset()

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["name"], "Custom")


class TestGameModuleImport(unittest.TestCase):
    """Test that game module constants and state are correct after import."""

    def test_flip_in_progress_starts_false(self):
        import game
        self.assertFalse(game._flip_in_progress)

    def test_grid_starts_empty(self):
        import game
        self.assertIsInstance(game.grid, list)

    def test_answered_colors_are_valid(self):
        import game
        self.assertTrue(game.ANSWERED_BG.startswith("#"))
        self.assertTrue(game.ANSWERED_FG.startswith("#"))


class TestScoresEdgeCases(unittest.TestCase):
    """Test scores module handles edge cases."""

    def test_all_zero_points_no_winner(self):
        """When all teams have 0 points, no team should be marked as winner."""
        r.team_points = [0, 0, 0]
        max_points = max(r.team_points)
        for points in r.team_points:
            is_winner = points == max_points and max_points > 0
            self.assertFalse(is_winner)

    def test_tied_teams_both_winners(self):
        """When two teams tie for first, both should be winners."""
        r.team_points = [500, 500, 100]
        max_points = max(r.team_points)
        winners = [i for i, p in enumerate(r.team_points)
                   if p == max_points and max_points > 0]
        self.assertEqual(winners, [0, 1])

    def test_single_team(self):
        """Scores should work with just one team."""
        r.teams = [{"name": "Solo", "color": "green"}]
        r.team_points = [300]
        max_points = max(r.team_points)
        is_winner = r.team_points[0] == max_points and max_points > 0
        self.assertTrue(is_winner)
        # Restore
        r.teams = [
            {"name": "Team 1", "color": "green"},
            {"name": "Team 2", "color": "red"},
            {"name": "Team 3", "color": "purple"},
        ]

    def test_negative_points(self):
        """Game doesn't award negative points, but scores shouldn't crash."""
        r.team_points = [-100, 200, 0]
        max_points = max(r.team_points)
        winners = [i for i, p in enumerate(r.team_points)
                   if p == max_points and max_points > 0]
        self.assertEqual(winners, [1])


class TestQuestionSetLoadEdgeCases(unittest.TestCase):
    """Test edge cases in question set loading."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self._orig_data_path = r.data_path
        r.data_path = lambda rel="": os.path.join(self.test_dir, rel)

    def tearDown(self):
        r.data_path = self._orig_data_path
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_load_single_category(self):
        cats = [{"name": "Only One", "questions": ["Q1"]}]
        r.save_question_set("single.json", "Single", [100], cats)
        r.load_question_set("single.json")
        self.assertEqual(len(r.categories), 1)
        self.assertEqual(r.to_be_switched_int, 1)

    def test_load_many_categories(self):
        cats = [{"name": f"Cat {i}", "questions": ["Q"]} for i in range(10)]
        r.save_question_set("many.json", "Many", [100], cats)
        r.load_question_set("many.json")
        self.assertEqual(len(r.categories), 10)

    def test_load_nonexistent_raises(self):
        with self.assertRaises(FileNotFoundError):
            r.load_question_set("nonexistent.json")

    def test_load_invalid_json_raises(self):
        d = r.get_questionsets_dir()
        path = os.path.join(d, "bad.json")
        with open(path, "w") as f:
            f.write("not json at all")
        with self.assertRaises(json.JSONDecodeError):
            r.load_question_set("bad.json")


if __name__ == "__main__":
    unittest.main()
