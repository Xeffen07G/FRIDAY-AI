import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
import asyncio
from unittest.mock import patch, MagicMock

from tools.tool_orchestrator import tool_orchestrator
from orchestrator.orchestrator import friday_orchestrator

class TestRealWorkflows(unittest.IsolatedAsyncioTestCase):
    @patch('tools.tool_registry.tool_registry.execute_tool')
    async def test_calculator_workflow(self, mock_execute):
        mock_execute.return_value = "100"
        
        # Test calculator intent resolution directly
        from orchestrator.action_chain_executor import action_chain_executor
        actions = action_chain_executor.parse_chain_deterministically("calculate 10*10")
        
        self.assertIsNotNone(actions)
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]['tool'], 'calculator')
        self.assertEqual(actions[0]['args']['expression'], '10*10')

    @patch('tools.tool_registry.tool_registry.execute_tool')
    async def test_vscode_launch_workflow(self, mock_execute):
        mock_execute.return_value = "VSCode launched."
        
        from orchestrator.action_chain_executor import action_chain_executor
        actions = action_chain_executor.parse_chain_deterministically("open vscode")
        
        self.assertIsNotNone(actions)
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]['tool'], 'system_action')
        self.assertEqual(actions[0]['args']['action'], 'open_app')
        self.assertEqual(actions[0]['args']['target'], 'vscode')

    @patch('tools.tool_registry.tool_registry.execute_tool')
    async def test_browser_launch_workflow(self, mock_execute):
        mock_execute.return_value = "Chrome launched."
        
        from orchestrator.action_chain_executor import action_chain_executor
        actions = action_chain_executor.parse_chain_deterministically("open chrome")
        
        self.assertIsNotNone(actions)
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]['tool'], 'system_action')
        self.assertEqual(actions[0]['args']['action'], 'open_app')
        self.assertEqual(actions[0]['args']['target'], 'chrome')

    @patch('tools.tool_registry.tool_registry.execute_tool')
    async def test_git_status_workflow(self, mock_execute):
        mock_execute.return_value = "On branch main. Nothing to commit."
        
        from orchestrator.action_chain_executor import action_chain_executor
        actions = action_chain_executor.parse_chain_deterministically("run git status")
        
        self.assertIsNotNone(actions)
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]['tool'], 'terminal')
        self.assertEqual(actions[0]['args']['command'], 'git status')

    @patch('tools.tool_registry.tool_registry.execute_tool')
    async def test_npm_install_workflow(self, mock_execute):
        mock_execute.return_value = "added 120 packages."
        
        from orchestrator.action_chain_executor import action_chain_executor
        actions = action_chain_executor.parse_chain_deterministically("run npm install")
        
        self.assertIsNotNone(actions)
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]['tool'], 'terminal')
        self.assertEqual(actions[0]['args']['command'], 'npm install')

    @patch('tools.tool_registry.tool_registry.execute_tool')
    async def test_multi_action_workflow(self, mock_execute):
        mock_execute.return_value = "success"
        
        from orchestrator.action_chain_executor import action_chain_executor
        actions = action_chain_executor.parse_chain_deterministically("open vscode and run npm install")
        
        self.assertIsNotNone(actions)
        self.assertEqual(len(actions), 2)
        self.assertEqual(actions[0]['tool'], 'system_action')
        self.assertEqual(actions[1]['tool'], 'terminal')
        self.assertEqual(actions[1]['args']['command'], 'npm install')

if __name__ == '__main__':
    unittest.main()
