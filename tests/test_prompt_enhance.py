import unittest
from unittest.mock import Mock, patch

import prompt_enhance


class PromptEnhanceTests(unittest.TestCase):
    def test_template_preserves_literal_braces(self):
        result = prompt_enhance._format_prompt(
            'Return JSON like {"subject": "{prompt}"}.', "a red fox"
        )
        self.assertEqual(result, 'Return JSON like {"subject": "a red fox"}.')

    @patch("prompt_enhance.requests.post")
    def test_basic_node_sends_openai_compatible_payload(self, post):
        response = Mock()
        response.json.return_value = {
            "choices": [{"message": {"content": "enhanced fox"}}]
        }
        post.return_value = response

        result = prompt_enhance.PromptEnhance().enhance_prompt(
            "fox", "https://example.test/v1/chat/completions", "test-key", "test-model"
        )

        self.assertEqual(result, ("enhanced fox",))
        self.assertEqual(post.call_args.kwargs["json"]["model"], "test-model")
        self.assertNotIn("test-key", str(post.call_args.kwargs["json"]))

    @patch("prompt_enhance.requests.post")
    def test_supports_api_key_header_without_bearer_prefix(self, post):
        response = Mock()
        response.json.return_value = {
            "choices": [{"message": {"content": "enhanced fox"}}]
        }
        post.return_value = response

        prompt_enhance.PromptEnhance().enhance_prompt(
            "fox", "https://example.test", "test-key", "test-model",
            api_key_header="api-key", api_key_prefix="",
        )

        self.assertEqual(post.call_args.kwargs["headers"]["api-key"], "test-key")

    @patch("prompt_enhance.requests.post")
    def test_advanced_node_adds_system_prompt_and_returns_original(self, post):
        response = Mock()
        response.json.return_value = {
            "choices": [{"message": {"content": "enhanced fox"}}]
        }
        post.return_value = response

        result = prompt_enhance.PromptEnhanceAdvanced().enhance_prompt_advanced(
            "fox", "https://example.test/v1/chat/completions", "test-key", "test-model",
            system_prompt="Be concise.", top_p=0.5,
        )

        self.assertEqual(result, ("enhanced fox", "fox"))
        self.assertEqual(post.call_args.kwargs["json"]["messages"][0]["role"], "system")
        self.assertEqual(post.call_args.kwargs["json"]["top_p"], 0.5)

    def test_rejects_malformed_response(self):
        response = Mock()
        response.json.return_value = {"choices": []}
        with self.assertRaisesRegex(ValueError, "did not include"):
            prompt_enhance._extract_enhanced_prompt(response)

    def test_rejects_missing_model_before_request(self):
        with self.assertRaisesRegex(ValueError, "model is required"):
            prompt_enhance.PromptEnhance().enhance_prompt(
                "fox", "https://example.test", "test-key", ""
            )


if __name__ == "__main__":
    unittest.main()
