from google.adk.models.lite_llm import LiteLlm

from agent_harness.agent import root_agent


def test_root_agent_uses_adk_and_exposes_expected_tools():
    assert root_agent.name == "patchpilot_coding_agent"
    assert isinstance(root_agent.model, LiteLlm)
    assert {tool.__name__ for tool in root_agent.tools} == {
        "check_task_contract",
        "inspect_workspace",
        "read_file",
        "write_file",
        "run_quality_gate",
    }
