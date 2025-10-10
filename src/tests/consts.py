TEST_USER_ID = "test-user-id"
TEST_KEY_ID = "test-key-id"
TEST_FXA_TOKEN = "test-fxa-token"
SUCCESSFUL_CHAT_RESPONSE = {
	"id": "2834283423498234",
	"created": 1750000000,
	"model": "test-model",
	"object": "chat.completion",
	"choices": [
		{
			"finish_reason": "stop",
			"index": 0,
			"message": {
				"content": "I'd be happy to help with that!",
				"role": "assistant",
			},
		}
	],
	"usage": {"completion_tokens": 27, "prompt_tokens": 18, "total_tokens": 45},
}
