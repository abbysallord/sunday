"""Tests for agent routing confidence scoring."""

import pytest
from unittest.mock import MagicMock, patch
from sunday.agents.manager import AgentManager, _score_agent


# --- Unit tests for the scoring function ---

def test_score_basic_match():
    assert _score_agent("search for news", ["search", "news"]) > 0

def test_score_negation_suppresses():
    # "don't remember" should not score for memory keywords
    score = _score_agent("i don't remember how to write a for loop", ["remember"])
    assert score < 0

def test_score_early_keyword_bonus():
    early = _score_agent("verify this claim", ["verify"])
    # keyword appears after position 40
    late = _score_agent("x" * 50 + " verify this claim", ["verify"])
    assert early > late

def test_score_multiword_bonus():
    multi = _score_agent("fact check this", ["fact check"])
    single = _score_agent("check this", ["check"])
    assert multi > single


# --- Integration routing tests via AgentManager ---

@pytest.fixture
def manager():
    mock_llm = MagicMock()
    return AgentManager(llm_router=mock_llm)


def test_routes_to_research(manager):
    agent = manager.determine_agent("search for the latest AI news")
    assert agent.info.id == "research_agent"

def test_routes_to_coding(manager):
    agent = manager.determine_agent("write a python script to parse a CSV file")
    assert agent.info.id == "coding_agent"

def test_routes_to_memory(manager):
    agent = manager.determine_agent("remember that my birthday is in July")
    assert agent.info.id == "memory_recall"

def test_routes_to_verification(manager):
    agent = manager.determine_agent("verify: the moon landing happened in 1969")
    assert agent.info.id == "verification"

def test_negation_routes_to_coding_not_memory(manager):
    # "don't remember" should NOT route to memory
    agent = manager.determine_agent("I don't remember how to write a for loop in Python")
    assert agent.info.id != "memory_recall"

def test_ambiguous_falls_back_to_secretary(manager):
    agent = manager.determine_agent("hello, how are you today?")
    assert agent.info.id == "secretary"

def test_routes_to_verification_on_fact_check(manager):
    agent = manager.determine_agent("fact check: the earth is flat")
    assert agent.info.id == "verification"

def test_routes_to_coding_on_file_operation(manager):
    agent = manager.determine_agent("read the file at /home/user/notes.txt")
    assert agent.info.id == "coding_agent"

def test_routes_to_research_on_who_is(manager):
    agent = manager.determine_agent("who is the current CEO of OpenAI?")
    assert agent.info.id == "research_agent"

def test_general_question_goes_to_secretary(manager):
    agent = manager.determine_agent("what is the meaning of life?")
    assert agent.info.id == "secretary"
