"""Tests for generated SAG Skill Markdown files."""

from types import SimpleNamespace

from shams_ai_gateway.tests.base_test import BaseAssistantTest
from shams_ai_gateway.utils.skill_file_manager import build_skill_markdown


class TestSkillMarkdownGeneration(BaseAssistantTest):
    def test_builds_canonical_frontmatter(self):
        skill = SimpleNamespace(
            skill_id="delete-document-usage",
            description="Delete documents safely.",
            content="# Delete documents\n\nFollow dependency checks.",
        )

        markdown = build_skill_markdown(skill)

        self.assertTrue(markdown.startswith("---\nname: delete-document-usage\n"))
        self.assertIn('description: "Delete documents safely."', markdown)
        self.assertIn("# Delete documents", markdown)

    def test_replaces_existing_frontmatter_without_duplication(self):
        skill = SimpleNamespace(
            skill_id="sales-analysis",
            description="Analyze ERPNext sales.",
            content=(
                "---\n"
                "name: old-name\n"
                "description: old description\n"
                "version: 1.0.0\n"
                "---\n\n"
                "# Sales workflow\n"
            ),
        )

        markdown = build_skill_markdown(skill)

        self.assertEqual(markdown.count("\n---"), 1)
        self.assertNotIn("old-name", markdown)
        self.assertNotIn("version:", markdown)
        self.assertIn("# Sales workflow", markdown)
