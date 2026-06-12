# ========= Copyright 2025-2026 @ Eigent.ai All Rights Reserved. =========
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ========= Copyright 2025-2026 @ Eigent.ai All Rights Reserved. =========
import os as _os
import platform

from camel.messages import BaseMessage
from camel.toolkits import ToolkitMessageIntegration

from app.agent.agent_model import agent_model
from app.agent.factory.remote_sub_agent import (
    attach_remote_sub_agent_if_enabled,
)
from app.agent.listen_chat_agent import logger
from app.agent.prompt import ACCOUNTING_SYS_PROMPT
from app.agent.toolkit.excel_toolkit import ExcelToolkit
from app.agent.toolkit.human_toolkit import HumanToolkit
from app.agent.toolkit.screenshot_toolkit import ScreenshotToolkit
from app.agent.toolkit.skill_toolkit import SkillToolkit
from app.agent.toolkit.terminal_toolkit import TerminalToolkit
from app.agent.utils import NOW_STR
from app.model.chat import Chat
from app.service.task import Agents
from app.utils.file_utils import get_working_directory


def _get_copilot_data_dir():
    # backend/app/agent/factory/accounting.py
    # -> up 4 levels -> project root -> copilot_data
    factory_dir = _os.path.dirname(_os.path.abspath(__file__))
    project_root = _os.path.dirname(  # project root
        _os.path.dirname(  # backend/
            _os.path.dirname(  # backend/app/
                _os.path.dirname(  # backend/app/agent/
                    factory_dir  # backend/app/agent/factory/
                )
            )
        )
    )
    return _os.path.join(project_root, "copilot_data")


def accounting_agent(options: Chat):
    working_directory = get_working_directory(options)
    logger.info(
        f"Creating accounting agent for project: {options.project_id} "
        f"in directory: {working_directory}"
    )

    message_integration = ToolkitMessageIntegration(
        message_handler=HumanToolkit(
            options.project_id, Agents.accounting_agent
        ).send_message_to_user
    )

    excel_toolkit = ExcelToolkit(
        options.project_id, working_directory=working_directory
    )
    excel_toolkit = message_integration.register_toolkits(excel_toolkit)

    screenshot_toolkit = ScreenshotToolkit(
        options.project_id,
        working_directory=working_directory,
        agent_name=Agents.accounting_agent,
    )
    # Save reference before registering for toolkits_to_register_agent
    screenshot_toolkit_for_agent_registration = screenshot_toolkit
    screenshot_toolkit = message_integration.register_toolkits(
        screenshot_toolkit
    )

    terminal_toolkit = TerminalToolkit(
        options.project_id,
        agent_name=Agents.accounting_agent,
        working_directory=working_directory,
        safe_mode=False,  # Accounting needs to run scripts
        clone_current_env=True,
    )
    terminal_toolkit = message_integration.register_toolkits(terminal_toolkit)

    skill_toolkit = SkillToolkit(
        options.project_id,
        Agents.accounting_agent,
        working_directory=working_directory,
        user_id=options.skill_config_user_id(),
    )
    skill_toolkit = message_integration.register_toolkits(skill_toolkit)

    tools = [
        *excel_toolkit.get_tools(),
        *screenshot_toolkit.get_tools(),
        *HumanToolkit.get_can_use_tools(
            options.project_id, Agents.accounting_agent
        ),
        *terminal_toolkit.get_tools(),
        *skill_toolkit.get_tools(),
    ]

    tool_names = [
        ExcelToolkit.toolkit_name(),
        ScreenshotToolkit.toolkit_name(),
        HumanToolkit.toolkit_name(),
        TerminalToolkit.toolkit_name(),
        SkillToolkit.toolkit_name(),
    ]

    copilot_data_dir = _get_copilot_data_dir()
    scripts_dir = _os.path.join(_os.path.dirname(copilot_data_dir), "scripts")

    system_message = ACCOUNTING_SYS_PROMPT.format(
        platform_system=platform.system(),
        platform_machine=platform.machine(),
        working_directory=working_directory,
        now_str=NOW_STR,
        copilot_data_dir=copilot_data_dir,
        scripts_dir=scripts_dir,
    )

    system_message = attach_remote_sub_agent_if_enabled(
        options=options,
        agent_name=Agents.accounting_agent,
        working_directory=working_directory,
        tools=tools,
        tool_names=tool_names,
        system_message=system_message,
        local_tool_description=(
            "local excel, terminal, file, or search tools"
        ),
        message_integration=message_integration,
    )

    return agent_model(
        Agents.accounting_agent,
        BaseMessage.make_assistant_message(
            role_name="Accounting Copilot",
            content=system_message,
        ),
        options,
        tools,
        tool_names=tool_names,
        toolkits_to_register_agent=[
            screenshot_toolkit_for_agent_registration,
        ],
    )
