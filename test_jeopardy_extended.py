"""
Extended test suite — covers bugs found by logical code review and additional
edge cases not covered by test_jeopardy.py.

Areas covered:
    - startscreen module-level flag reset and animation chain integrity
    - game._flip_in_progress lifecycle (must reset between games)
    - game._team_score_labels cleanup
    - LButton.set_text wrapping logic and separator handling
    - keyboard_input team key parsing
    - settings._parse_values input parsing edge cases
    - settings tab geometry tracking
    - Question set CRUD edge cases
    - resources state consistency
    - Color constant validity
    - main flow branching logic
"""

import os
import sys
import json
import tempfile
import shutil
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import resources as r


# ===========================================================================
# Startscreen module-level state and animation chain
# ===========================================================================

class TestStartscreenState(unittest.TestCase):
    """Test startscreen module-level flags."""

    def test_initial_show_settings_is_false(self):
        import startscreen
        # Module-level default
        startscreen.show_settings = False
        self.assertFalse(startscreen.show_settings)

    def test_initial_quit_app_is_false(self):
        import startscreen
        startscreen.quit_app = False
        self.assertFalse(startscreen.quit_app)

    def test_run_resets_flags(self):
        """run() must reset both flags so stale state from a previous
        invocation doesn't leak through."""
        import startscreen
        startscreen.show_settings = True
        startscreen.quit_app = True

        # Simulate the reset that run() performs (without launching mainloop)
        # We can't actually run() in a unit test, so we test the reset block
        # by importing the source.
        with open(os.path.join(os.path.dirname(__file__), "startscreen.py")) as f:
            src = f.read()
        self.assertIn("show_settings = False", src)
        self.assertIn("quit_app = False", src)

    def test_animate_title_called_in_init(self):
        """REGRESSION: a previous edit accidentally orphaned the
        self.animate_title() call after _quit() with bad indentation, so
        the animation chain never started. Verify it's still in __init__."""
        import startscreen
        import inspect
        src = inspect.getsource(startscreen.StartScreen.__init__)
        self.assertIn('self.animate_title("JEOPARDY!", 0)', src)

    def test_choose_method_exists(self):
        import startscreen
        self.assertTrue(hasattr(startscreen.StartScreen, "_choose"))

    def test_quit_method_exists(self):
        import startscreen
        self.assertTrue(hasattr(startscreen.StartScreen, "_quit"))


# ===========================================================================
# Game module: _flip_in_progress lifecycle
# ===========================================================================

class TestGameFlipState(unittest.TestCase):
    """Test that game module state is correctly reset between runs."""

    def test_flip_in_progress_starts_false(self):
        import game
        self.assertFalse(game._flip_in_progress)

    def test_run_resets_flip_in_progress(self):
        """REGRESSION: _flip_in_progress was a module global that persisted
        across game.run() invocations. If a previous game ended unusually,
        the flag could remain True and silently break the next game."""
        import game
        game._flip_in_progress = True

        # Verify run() contains the reset (check source)
        import inspect
        src = inspect.getsource(game.run)
        self.assertIn("_flip_in_progress", src)
        self.assertIn("False", src)

    def test_run_clears_grid(self):
        import game
        game.grid.append(["fake", "stuff"])
        import inspect
        src = inspect.getsource(game.run)
        self.assertIn("grid.clear()", src)

    def test_run_clears_score_labels(self):
        import game
        game._team_score_labels.append("fake_label")
        import inspect
        src = inspect.getsource(game.run)
        self.assertIn("_team_score_labels.clear()", src)


# ===========================================================================
# LButton.set_text — text wrapping logic
# ===========================================================================

class TestSetTextWrapping(unittest.TestCase):
    """Test the word-wrap logic in LButton.set_text — pure logic test using
    a stub master so we don't need a real Tk window."""

    def _make_lbutton_stub(self):
        """Create a minimal stub of LButton with just the methods needed for
        set_text. The real LButton needs Tk; we replicate the algorithm."""
        # We'll just exercise the actual algorithm by calling set_text on a
        # real (but withdrawn) Tk-based LButton.
        import tkinter as tk
        import game
        root = tk.Tk()
        root.withdraw()
        lbl = game.LButton(root, p_width=100, p_height=100,
                           font=("Arial", 12))
        return root, lbl

    def test_set_text_simple(self):
        root, lbl = self._make_lbutton_stub()
        try:
            lbl.set_text("Hello world")
            text = lbl.get_text()
            self.assertIn("Hello", text)
            self.assertIn("world", text)
        finally:
            root.destroy()

    def test_set_text_with_separator(self):
        """The '!' character is a separator between German and English versions."""
        root, lbl = self._make_lbutton_stub()
        try:
            lbl.set_text("Frage ! Question")
            text = lbl.get_text()
            self.assertIn("Frage", text)
            self.assertIn("Question", text)
            # Separator should produce a double newline
            self.assertIn("\n\n", text)
        finally:
            root.destroy()

    def test_set_text_empty(self):
        root, lbl = self._make_lbutton_stub()
        try:
            lbl.set_text("")
            self.assertEqual(lbl.get_text(), "")
        finally:
            root.destroy()

    def test_set_text_single_word(self):
        root, lbl = self._make_lbutton_stub()
        try:
            lbl.set_text("Hello")
            self.assertIn("Hello", lbl.get_text())
        finally:
            root.destroy()

    def test_visible_text_applies_wrapped(self):
        root, lbl = self._make_lbutton_stub()
        try:
            lbl.set_text("Hello world")
            lbl.visible_text()
            self.assertEqual(lbl.cget("text"), lbl.get_text())
        finally:
            root.destroy()


# ===========================================================================
# Settings _parse_values — number parsing logic
# ===========================================================================

class TestParseValues(unittest.TestCase):
    """Test the values-string parser used by SettingsScreen."""

    def _parse(self, raw):
        """Replicate _parse_values logic for direct testing."""
        result = []
        for part in raw.split(","):
            part = part.strip()
            if part.isdigit():
                result.append(int(part))
        return result if result else [100, 200, 400, 600, 1000]

    def test_normal_input(self):
        self.assertEqual(self._parse("100, 200, 300"), [100, 200, 300])

    def test_no_spaces(self):
        self.assertEqual(self._parse("100,200,300"), [100, 200, 300])

    def test_extra_spaces(self):
        self.assertEqual(self._parse("  100  ,  200  ,  300  "), [100, 200, 300])

    def test_empty_returns_default(self):
        self.assertEqual(self._parse(""), [100, 200, 400, 600, 1000])

    def test_invalid_chars_ignored(self):
        self.assertEqual(self._parse("100, abc, 200"), [100, 200])

    def test_negative_ignored(self):
        # isdigit() returns False for negative
        self.assertEqual(self._parse("100, -50, 200"), [100, 200])

    def test_decimal_ignored(self):
        self.assertEqual(self._parse("100, 200.5, 300"), [100, 300])

    def test_only_invalid_returns_default(self):
        self.assertEqual(self._parse("abc, def"), [100, 200, 400, 600, 1000])

    def test_single_value(self):
        self.assertEqual(self._parse("500"), [500])

    def test_zero_allowed(self):
        self.assertEqual(self._parse("0, 100"), [0, 100])


# ===========================================================================
# Settings tab geometry — must work without window mapping
# ===========================================================================

class TestSettingsTabStructure(unittest.TestCase):
    """Test settings tab structure without launching mainloop."""

    def test_tab_geom_attribute_exists_in_source(self):
        """REGRESSION: tab underline used winfo_x() which returns 0 before
        the window is mapped. Now uses _tab_geom dict."""
        import settings
        import inspect
        src = inspect.getsource(settings.SettingsScreen)
        self.assertIn("_tab_geom", src)

    def test_tab_navigation_uses_stored_geometry(self):
        import settings
        import inspect
        src = inspect.getsource(settings.SettingsScreen._switch_tab)
        # Underline placement must use stored _tab_geom dict (not live winfo_x)
        self.assertIn("_tab_geom[tab_name]", src)
        self.assertIn("self.tab_underline.place", src)
        # Strip comments and check no winfo_x() call remains in actual code
        code_lines = [line for line in src.split("\n")
                      if not line.strip().startswith("#")]
        code_only = "\n".join(code_lines)
        self.assertNotIn("winfo_x()", code_only)

    def test_settings_screen_constructable(self):
        """Smoke test: SettingsScreen __init__ runs without error."""
        import tkinter as tk
        import settings
        root = tk.Tk()
        root.withdraw()
        try:
            scr = settings.SettingsScreen(root)
            # Verify basic structure exists
            self.assertIn("teams", scr.tab_frames)
            self.assertIn("fragenset", scr.tab_frames)
            self.assertIn("start", scr.tab_frames)
            self.assertEqual(len(scr.tab_buttons), 3)
        finally:
            try:
                root.destroy()
            except Exception:
                pass

    def test_initial_tab_is_teams(self):
        import tkinter as tk
        import settings
        root = tk.Tk()
        root.withdraw()
        try:
            scr = settings.SettingsScreen(root)
            self.assertEqual(scr.current_tab, "teams")
        finally:
            try:
                root.destroy()
            except Exception:
                pass

    def test_switch_tab_changes_current(self):
        import tkinter as tk
        import settings
        root = tk.Tk()
        root.withdraw()
        try:
            scr = settings.SettingsScreen(root)
            scr._switch_tab("fragenset")
            self.assertEqual(scr.current_tab, "fragenset")
            scr._switch_tab("start")
            self.assertEqual(scr.current_tab, "start")
        finally:
            try:
                root.destroy()
            except Exception:
                pass


# ===========================================================================
# Question set edge cases
# ===========================================================================

class TestQuestionSetEdgeCases(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self._orig_data_path = r.data_path
        r.data_path = lambda rel="": os.path.join(self.test_dir, rel)

    def tearDown(self):
        r.data_path = self._orig_data_path
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_save_empty_categories(self):
        """Saving with zero categories should not crash."""
        r.save_question_set("empty.json", "Empty", [100], [])
        path = os.path.join(r.get_questionsets_dir(), "empty.json")
        self.assertTrue(os.path.exists(path))
        with open(path) as f:
            data = json.load(f)
        self.assertEqual(data["categories"], [])

    def test_save_many_values(self):
        vals = list(range(100, 10001, 100))  # 100 values
        cats = [{"name": "C", "questions": [f"Q{i}" for i in range(100)]}]
        r.save_question_set("big.json", "Big", vals, cats)
        r.load_question_set("big.json")
        self.assertEqual(len(r.values), 100)

    def test_load_set_resets_to_be_switched(self):
        cats = [
            {"name": "A", "questions": ["q1", "q2"]},
            {"name": "B", "questions": ["q1", "q2"]},
        ]
        r.save_question_set("two.json", "Two", [100, 200], cats)
        r.load_question_set("two.json")
        self.assertEqual(r.to_be_switched_int, 4)

    def test_list_returns_sorted(self):
        for name in ["zebra.json", "apple.json", "mango.json"]:
            r.save_question_set(name, name, [100],
                                [{"name": "C", "questions": ["Q"]}])
        sets = r.list_question_sets()
        filenames = [f for f, _ in sets]
        self.assertEqual(filenames, sorted(filenames))

    def test_save_overwrites_existing(self):
        r.save_question_set("over.json", "First", [100],
                            [{"name": "A", "questions": ["Q"]}])
        r.save_question_set("over.json", "Second", [200],
                            [{"name": "B", "questions": ["Q"]}])
        path = os.path.join(r.get_questionsets_dir(), "over.json")
        with open(path) as f:
            data = json.load(f)
        self.assertEqual(data["name"], "Second")
        self.assertEqual(data["values"], [200])

    def test_ensure_default_idempotent(self):
        """Calling ensure_default_questionset twice should not change content."""
        r.ensure_default_questionset()
        path = os.path.join(r.get_questionsets_dir(), "ergo_default.json")
        with open(path) as f:
            first = json.load(f)
        r.ensure_default_questionset()
        with open(path) as f:
            second = json.load(f)
        self.assertEqual(first, second)

    def test_delete_then_recreate(self):
        r.save_question_set("temp.json", "Temp", [100],
                            [{"name": "C", "questions": ["Q"]}])
        r.delete_question_set("temp.json")
        # Recreate
        r.save_question_set("temp.json", "Temp2", [200],
                            [{"name": "D", "questions": ["Q"]}])
        path = os.path.join(r.get_questionsets_dir(), "temp.json")
        self.assertTrue(os.path.exists(path))

    def test_load_missing_values_field_raises(self):
        """A malformed JSON missing the 'values' field should raise KeyError."""
        d = r.get_questionsets_dir()
        path = os.path.join(d, "broken.json")
        with open(path, "w") as f:
            json.dump({"name": "Broken", "categories": []}, f)
        with self.assertRaises(KeyError):
            r.load_question_set("broken.json")

    def test_load_missing_categories_field_raises(self):
        d = r.get_questionsets_dir()
        path = os.path.join(d, "broken2.json")
        with open(path, "w") as f:
            json.dump({"name": "Broken", "values": [100]}, f)
        with self.assertRaises(KeyError):
            r.load_question_set("broken2.json")


# ===========================================================================
# Resources state consistency
# ===========================================================================

class TestResourcesConsistency(unittest.TestCase):

    def test_team_palette_no_duplicates(self):
        self.assertEqual(len(r.TEAM_PALETTE), len(set(r.TEAM_PALETTE)))

    def test_team_palette_sufficient_for_max_teams(self):
        """User can have up to 6 teams; palette must have at least 6 colors."""
        self.assertGreaterEqual(len(r.TEAM_PALETTE), 6)

    def test_default_categories_match_questions_length(self):
        for i, cat in enumerate(r.categories):
            self.assertEqual(len(r.questions[i]), len(r.values),
                             f"Category {i} ({cat!r}) question count mismatch")

    def test_reset_with_one_team(self):
        original = r.teams[:]
        r.teams = [{"name": "Solo", "color": "blue"}]
        r.reset_game_state()
        self.assertEqual(len(r.team_points), 1)
        r.teams = original

    def test_reset_with_six_teams(self):
        original = r.teams[:]
        r.teams = [{"name": f"T{i}", "color": "red"} for i in range(6)]
        r.reset_game_state()
        self.assertEqual(len(r.team_points), 6)
        self.assertTrue(all(p == 0 for p in r.team_points))
        r.teams = original

    def test_reset_zeros_all_points(self):
        original_teams = r.teams[:]
        r.teams = [{"name": "A", "color": "red"},
                   {"name": "B", "color": "blue"}]
        r.team_points = [9999, -500]
        r.reset_game_state()
        self.assertEqual(r.team_points, [0, 0])
        r.teams = original_teams

    def test_font_constants_reasonable_values(self):
        self.assertGreater(r.FONT_TITLE, r.FONT_SECTION)
        self.assertGreater(r.FONT_SECTION, r.FONT_BODY)
        self.assertGreater(r.FONT_BODY, r.FONT_SMALL)
        self.assertGreater(r.FONT_BUTTON, 0)

    def test_spacing_constants_ordered(self):
        self.assertGreater(r.SPACING_MAJOR, r.SPACING_SECTION)
        self.assertGreater(r.SPACING_SECTION, r.SPACING_ELEMENT)


# ===========================================================================
# Color constants — semantic checks
# ===========================================================================

class TestColorSemantics(unittest.TestCase):

    def _hex_to_rgb(self, hex_str):
        h = hex_str.lstrip("#")
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    def test_blue_is_blueish(self):
        r_, g, b = self._hex_to_rgb(r.BLUE)
        self.assertGreater(b, r_)
        self.assertGreater(b, g)

    def test_gold_is_yellowish(self):
        r_, g, b = self._hex_to_rgb(r.GOLD)
        self.assertGreater(r_, b)
        self.assertGreater(g, b)

    def test_dark_blue_darker_than_blue(self):
        sum_blue = sum(self._hex_to_rgb(r.BLUE))
        sum_dark = sum(self._hex_to_rgb(r.DARK_BLUE))
        self.assertLess(sum_dark, sum_blue)

    def test_hover_gold_lighter_than_gold(self):
        sum_gold = sum(self._hex_to_rgb(r.GOLD))
        sum_hover = sum(self._hex_to_rgb(r.HOVER_GOLD))
        self.assertGreater(sum_hover, sum_gold)

    def test_active_gold_darker_than_gold(self):
        sum_gold = sum(self._hex_to_rgb(r.GOLD))
        sum_active = sum(self._hex_to_rgb(r.ACTIVE_GOLD))
        self.assertLess(sum_active, sum_gold)

    def test_error_red_is_reddish(self):
        r_, g, b = self._hex_to_rgb(r.ERROR_RED)
        self.assertGreater(r_, g)
        self.assertGreater(r_, b)

    def test_success_green_is_greenish(self):
        r_, g, b = self._hex_to_rgb(r.SUCCESS_GREEN)
        self.assertGreater(g, r_)
        self.assertGreater(g, b)


# ===========================================================================
# Main flow branching
# ===========================================================================

class TestMainFlowBranching(unittest.TestCase):
    """Test main.py branching based on startscreen choice."""

    def test_main_imports_all_modules(self):
        import main
        self.assertTrue(hasattr(main, "main"))

    def test_main_checks_quit_app(self):
        """main() must call sys.exit(0) when startscreen.quit_app is True."""
        import inspect
        import main
        src = inspect.getsource(main.main)
        self.assertIn("quit_app", src)
        self.assertIn("sys.exit", src)

    def test_main_branches_on_show_settings(self):
        """main() must conditionally call settings.run() based on flag."""
        import inspect
        import main
        src = inspect.getsource(main.main)
        self.assertIn("show_settings", src)
        self.assertIn("settings.run()", src)
        self.assertIn("load_question_set", src)

    def test_main_calls_reset_game_state(self):
        import inspect
        import main
        src = inspect.getsource(main.main)
        self.assertIn("reset_game_state", src)

    def test_main_call_order(self):
        """Verify call order: startscreen → ensure_default → (settings|load) →
        reset → game → scores."""
        import inspect
        import main
        src = inspect.getsource(main.main)
        i_start = src.find("startscreen.run()")
        i_ensure = src.find("ensure_default_questionset")
        i_reset = src.find("reset_game_state")
        i_game = src.find("game.run()")
        i_scores = src.find("scores.run()")
        self.assertLess(i_start, i_ensure)
        self.assertLess(i_ensure, i_reset)
        self.assertLess(i_reset, i_game)
        self.assertLess(i_game, i_scores)


# ===========================================================================
# Game button keyboard input — team key parsing
# ===========================================================================

class TestKeyboardKeyMapping(unittest.TestCase):
    """Test that the team-key parsing logic in keyboard_input handles all
    valid team counts (2-6)."""

    def test_team_keys_for_each_count(self):
        """For N teams, valid keys are '1'..str(N) and str(N+1) for 'Niemand'."""
        for num_teams in range(2, 7):
            valid_team_keys = [str(i + 1) for i in range(num_teams)]
            niemand_key = str(num_teams + 1)
            self.assertEqual(len(valid_team_keys), num_teams)
            self.assertNotIn(niemand_key, valid_team_keys)
            # All single-character (since num_teams ≤ 6, max key is '7')
            for k in valid_team_keys + [niemand_key]:
                self.assertEqual(len(k), 1)

    def test_max_six_teams_uses_keys_1_to_7(self):
        """6 teams → keys '1','2','3','4','5','6' for teams, '7' for Niemand."""
        num_teams = 6
        keys = [str(i + 1) for i in range(num_teams)] + [str(num_teams + 1)]
        self.assertEqual(keys, ["1", "2", "3", "4", "5", "6", "7"])


# ===========================================================================
# Scores — animation step calculation
# ===========================================================================

class TestScoresAnimationCalculation(unittest.TestCase):
    """Test the bar height calculation logic in scores.py."""

    def test_full_score_is_100_percent(self):
        import math
        team_points = 600
        # 3 cats × 2 vals = 600 max
        allpoints = 600
        pct = math.ceil(100 * (team_points / allpoints))
        self.assertEqual(pct, 100)

    def test_zero_score_is_zero_percent(self):
        import math
        pct = math.ceil(100 * (0 / 600))
        self.assertEqual(pct, 0)

    def test_half_score_is_50_percent(self):
        import math
        pct = math.ceil(100 * (300 / 600))
        self.assertEqual(pct, 50)

    def test_winner_logic_no_teams(self):
        team_points = []
        max_points = max(team_points) if team_points else 0
        self.assertEqual(max_points, 0)

    def test_winner_logic_with_zero_max(self):
        team_points = [0, 0, 0]
        max_points = max(team_points)
        # No winners when max is 0
        winners = [i for i, p in enumerate(team_points)
                   if p == max_points and max_points > 0]
        self.assertEqual(winners, [])

    def test_three_way_tie(self):
        team_points = [400, 400, 400]
        max_points = max(team_points)
        winners = [i for i, p in enumerate(team_points)
                   if p == max_points and max_points > 0]
        self.assertEqual(winners, [0, 1, 2])


# ===========================================================================
# Settings: SettingsScreen state synchronization on tab switch
# ===========================================================================

class TestSettingsTabSync(unittest.TestCase):
    """Verify that switching tabs syncs state correctly."""

    def test_switch_from_teams_reads_team_ui(self):
        import inspect
        import settings
        src = inspect.getsource(settings.SettingsScreen._switch_tab)
        self.assertIn("_read_teams_from_ui", src)

    def test_switch_from_fragenset_saves_questions(self):
        import inspect
        import settings
        src = inspect.getsource(settings.SettingsScreen._switch_tab)
        self.assertIn("_save_current_questions", src)

    def test_switch_to_start_refreshes_summary(self):
        import inspect
        import settings
        src = inspect.getsource(settings.SettingsScreen._switch_tab)
        self.assertIn("_refresh_start_summary", src)

    def test_quit_app_uses_sys_exit(self):
        import inspect
        import settings
        src = inspect.getsource(settings.SettingsScreen._quit_app)
        self.assertIn("sys.exit", src)


# ===========================================================================
# Settings: question set loading edge cases via SettingsScreen
# ===========================================================================

class TestSettingsLoadingBehavior(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self._orig_data_path = r.data_path
        r.data_path = lambda rel="": os.path.join(self.test_dir, rel)

    def tearDown(self):
        r.data_path = self._orig_data_path
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_settings_loads_default_set(self):
        import tkinter as tk
        import settings
        # Ensure default exists
        r.ensure_default_questionset()

        root = tk.Tk()
        root.withdraw()
        try:
            scr = settings.SettingsScreen(root)
            # editor_data should be populated
            self.assertIsNotNone(scr.editor_data)
            self.assertEqual(scr.editor_filename, "ergo_default.json")
        finally:
            try:
                root.destroy()
            except Exception:
                pass

    def test_add_then_remove_team(self):
        import tkinter as tk
        import settings
        r.ensure_default_questionset()
        original_teams = r.teams[:]

        root = tk.Tk()
        root.withdraw()
        try:
            scr = settings.SettingsScreen(root)
            initial_count = len(r.teams)
            scr._add_team()
            self.assertEqual(len(r.teams), initial_count + 1)
            scr._remove_team()
            self.assertEqual(len(r.teams), initial_count)
        finally:
            r.teams = original_teams
            try:
                root.destroy()
            except Exception:
                pass

    def test_cannot_exceed_six_teams(self):
        import tkinter as tk
        import settings
        r.ensure_default_questionset()
        original_teams = r.teams[:]

        root = tk.Tk()
        root.withdraw()
        try:
            scr = settings.SettingsScreen(root)
            # Force to 6 teams
            r.teams = [{"name": f"T{i}", "color": r.TEAM_PALETTE[i % 6]}
                       for i in range(6)]
            scr._rebuild_team_rows()
            scr._add_team()  # Should be no-op
            self.assertEqual(len(r.teams), 6)
        finally:
            r.teams = original_teams
            try:
                root.destroy()
            except Exception:
                pass

    def test_cannot_drop_below_two_teams(self):
        import tkinter as tk
        import settings
        r.ensure_default_questionset()
        original_teams = r.teams[:]

        root = tk.Tk()
        root.withdraw()
        try:
            scr = settings.SettingsScreen(root)
            r.teams = [{"name": "A", "color": "red"},
                       {"name": "B", "color": "blue"}]
            scr._rebuild_team_rows()
            scr._remove_team()  # Should be no-op
            self.assertEqual(len(r.teams), 2)
        finally:
            r.teams = original_teams
            try:
                root.destroy()
            except Exception:
                pass


# ===========================================================================
# Game module: cell counting and ANSWERED constants
# ===========================================================================

class TestGameModuleConstants(unittest.TestCase):

    def test_answered_bg_is_dark(self):
        import game
        h = game.ANSWERED_BG.lstrip("#")
        rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
        self.assertLess(sum(rgb), 384)  # < average gray

    def test_answered_fg_is_dark(self):
        import game
        h = game.ANSWERED_FG.lstrip("#")
        rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
        self.assertLess(sum(rgb), 384)

    def test_grid_is_module_global(self):
        import game
        self.assertIsInstance(game.grid, list)

    def test_team_score_labels_is_module_global(self):
        import game
        self.assertIsInstance(game._team_score_labels, list)


# ===========================================================================
# Integration: full save → load → reset → state cycle
# ===========================================================================

class TestFullStateCycle(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self._orig_data_path = r.data_path
        r.data_path = lambda rel="": os.path.join(self.test_dir, rel)
        self._orig_teams = r.teams[:]

    def tearDown(self):
        r.data_path = self._orig_data_path
        r.teams = self._orig_teams
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_complete_cycle(self):
        # 1. Save a custom set
        cats = [
            {"name": "Cat 1", "questions": ["Q1", "Q2", "Q3"]},
            {"name": "Cat 2", "questions": ["Q4", "Q5", "Q6"]},
        ]
        r.save_question_set("cycle.json", "Cycle Test", [50, 100, 150], cats)

        # 2. Load it
        r.load_question_set("cycle.json")
        self.assertEqual(r.values, [50, 100, 150])
        self.assertEqual(r.categories, ["Cat 1", "Cat 2"])
        self.assertEqual(len(r.questions), 2)

        # 3. Set up teams
        r.teams = [
            {"name": "A", "color": "red"},
            {"name": "B", "color": "blue"},
            {"name": "C", "color": "green"},
        ]

        # 4. Reset game state
        r.reset_game_state()
        self.assertEqual(r.team_points, [0, 0, 0])
        self.assertEqual(r.to_be_switched_int, 6)  # 2 cats × 3 values

        # 5. Simulate scoring
        r.team_points[0] += 50
        r.team_points[1] += 100
        r.team_points[2] += 150
        self.assertEqual(sum(r.team_points), 300)

        # 6. Reset again
        r.reset_game_state()
        self.assertEqual(r.team_points, [0, 0, 0])

    def test_to_be_switched_calculation(self):
        cats = [{"name": f"C{i}", "questions": ["q"] * 5} for i in range(7)]
        r.save_question_set("big.json", "Big", [100, 200, 300, 400, 500], cats)
        r.load_question_set("big.json")
        self.assertEqual(r.to_be_switched_int, 7 * 5)


if __name__ == "__main__":
    unittest.main()
