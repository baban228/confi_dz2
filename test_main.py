import unittest
from unittest.mock import patch, mock_open
import subprocess
import json
import os
from main import build_dependency_graph
from main import (
    run_git_command,
    get_commit_history,
    get_files_changed_between_commits,
    build_dependency_graph,
    generate_mermaid_graph,
    save_graph_to_file,
    main
)


class TestGitOperations(unittest.TestCase):

    @patch('subprocess.run')
    def test_run_git_command_success(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(args=['git', 'log'], returncode=0,
                                                            stdout='commit1\ncommit2', stderr='')
        result = run_git_command(['git', 'log'], '/repo')

        self.assertEqual(result, 'commit1\ncommit2')
        mock_run.assert_called_once_with(['git', 'log'], cwd='/repo', capture_output=True, text=True)

    @patch('subprocess.run')
    def test_run_git_command_failure(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(args=['git', 'log'], returncode=1, stdout='',
                                                            stderr='error')

        with self.assertRaises(Exception) as context:
            run_git_command(['git', 'log'], '/repo')

        self.assertTrue('Git command failed: error' in str(context.exception))


class TestGitLogOperations(unittest.TestCase):

    @patch('main.run_git_command')
    def test_get_commit_history(self, mock_run_git_command):
        mock_run_git_command.return_value = 'commit1\ncommit2\ncommit3'

        commits = get_commit_history('v1.0', '/repo')
        self.assertEqual(commits, ['commit1', 'commit2', 'commit3'])
        mock_run_git_command.assert_called_once_with(['git', 'log', '--pretty=format:%H', 'v1.0'], '/repo')


class TestFileChangesBetweenCommits(unittest.TestCase):

    @patch('main.run_git_command')
    def test_get_files_changed_between_commits(self, mock_run_git_command):
        mock_run_git_command.return_value = 'file1.txt\nfile2.txt'

        changed_files = get_files_changed_between_commits('commit1', 'commit2', '/repo')

        self.assertEqual(changed_files, ['file1.txt', 'file2.txt'])
        mock_run_git_command.assert_called_once_with(['git', 'diff', '--name-only', 'commit1', 'commit2'], '/repo')



class TestMermaidGraphGeneration(unittest.TestCase):

    def test_generate_mermaid_graph(self):
        dependencies = {
            'commit1': ['file1.txt', 'file2.txt'],
            'commit2': ['file3.txt']
        }

        graph_code = generate_mermaid_graph(dependencies)
        expected_graph = '''graph TD
    commit1 --> file1.txt
    commit1 --> file2.txt
    commit2 --> file3.txt
'''
        self.assertEqual(graph_code, expected_graph)


class TestSaveGraphToFile(unittest.TestCase):

    @patch('builtins.open', new_callable=mock_open)
    def test_save_graph_to_file(self, mock_file):
        graph_code = 'graph TD\n    commit1 --> file1.txt\n'
        output_file = 'output.mmd'
        save_graph_to_file(graph_code, output_file)

        mock_file.assert_called_once_with(output_file, 'w')
        mock_file().write.assert_called_once_with(graph_code)


class TestMainFunction(unittest.TestCase):

    @patch('builtins.open', new_callable=mock_open, read_data=json.dumps({
        'repository_path': '/repo',
        'tag_name': 'v1.0',
        'output_file': 'output.mmd'
    }))
    @patch('main.build_dependency_graph')
    @patch('main.generate_mermaid_graph')
    @patch('main.save_graph_to_file')
    def test_main(self, mock_save_graph_to_file, mock_generate_mermaid_graph, mock_build_dependency_graph, mock_open):
        mock_build_dependency_graph.return_value = {'commit1': ['file1.txt']}
        mock_generate_mermaid_graph.return_value = 'graph TD\n    commit1 --> file1.txt\n'

        main('config.json')

        mock_open.assert_called_once_with('config.json', 'r')
        mock_build_dependency_graph.assert_called_once_with('v1.0', '/repo')
        mock_generate_mermaid_graph.assert_called_once_with({'commit1': ['file1.txt']})
        mock_save_graph_to_file.assert_called_once_with('graph TD\n    commit1 --> file1.txt\n', 'output.mmd')


if __name__ == '__main__':
    unittest.main()
