"""Engineering crew wired the same way as the uv project, without uv."""

from __future__ import annotations

import engineering_team.vscode_optimized.patch  # noqa: F401
from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task

from engineering_team.vscode_optimized.tools.sandbox_tools import sandbox_tools

_CONTEXT7 = "https://mcp.context7.com/mcp"


@CrewBase
class EngineeringTeam:
    """EngineeringTeam crew."""

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def engineering_lead(self) -> Agent:
        return Agent(
            config=self.agents_config["engineering_lead"],
            verbose=True,
            mcps=[_CONTEXT7],
        )

    @agent
    def backend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["backend_engineer"],
            verbose=True,
            tools=sandbox_tools,
            mcps=[_CONTEXT7],
        )

    @agent
    def frontend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["frontend_engineer"],
            verbose=True,
            tools=sandbox_tools,
            mcps=[_CONTEXT7],
        )

    @agent
    def test_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["test_engineer"],
            verbose=True,
            tools=sandbox_tools,
            mcps=[_CONTEXT7],
        )

    @task
    def design_task(self) -> Task:
        return Task(config=self.tasks_config["design_task"])

    @task
    def code_task(self) -> Task:
        return Task(config=self.tasks_config["code_task"])

    @task
    def frontend_task(self) -> Task:
        return Task(config=self.tasks_config["frontend_task"])

    @task
    def test_task(self) -> Task:
        return Task(config=self.tasks_config["test_task"])

    @crew
    def crew(self) -> Crew:
        """Create the sequential engineering crew."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
