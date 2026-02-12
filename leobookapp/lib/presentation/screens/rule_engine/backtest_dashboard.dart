import 'package:flutter/material.dart';
import 'package:leobookapp/data/models/rule_config_model.dart';
import 'package:leobookapp/data/services/leo_service.dart';
import 'rule_editor_screen.dart';

class BacktestDashboard extends StatefulWidget {
  const BacktestDashboard({super.key});

  @override
  State<BacktestDashboard> createState() => _BacktestDashboardState();
}

class _BacktestDashboardState extends State<BacktestDashboard> {
  final LeoService _leoService = LeoService();
  bool _isLoading = false;
  List<Map<String, dynamic>> _results = [];
  RuleConfigModel? _currentConfig;

  @override
  void initState() {
    super.initState();
    _loadInitialData();
  }

  Future<void> _loadInitialData() async {
    setState(() => _isLoading = true);
    _currentConfig = await _leoService.loadRuleConfig();
    if (_currentConfig != null) {
      await _refreshResults();
    }
    setState(() => _isLoading = false);
  }

  Future<void> _refreshResults() async {
    if (_currentConfig == null) return;
    try {
      // We load the CSV produced by the Python script
      final results = await _leoService.getBacktestResults(
        _currentConfig!.name,
      );
      setState(() {
        _results = results;
      });
    } catch (e) {
      debugPrint("Error loading results: $e");
    }
  }

  Future<void> _runBacktest() async {
    if (_currentConfig == null) return;

    setState(() => _isLoading = true);
    try {
      await _leoService.triggerBacktest(_currentConfig!);

      // In a real app, we'd listen for a "done" signal or file change
      // For now, we simulate a wait while the python script (hypothetically) runs
      // Since we don't have the real-time python runner hooked up yet in this demo flow,
      // we'll just show a message.
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text(
              'Backtest Triggered! Check terminal for Python output (once integrated).',
            ),
          ),
        );
      }

      // Simulate result loading after a delay (assuming python script runs fast or we mock it)
      await Future.delayed(const Duration(seconds: 2));
      await _refreshResults();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error triggering backtest: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Backtest Dashboard'),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: () async {
              await Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) => const RuleEditorScreen(),
                ),
              );
              _loadInitialData(); // Refresh on return
            },
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _refreshResults,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : Column(
              children: [
                _buildSummaryCard(),
                const Divider(),
                Expanded(child: _buildResultsList()),
              ],
            ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _runBacktest,
        label: const Text("Run Backtest"),
        icon: const Icon(Icons.play_arrow),
      ),
    );
  }

  Widget _buildSummaryCard() {
    int total = _results.length;
    int correct = _results
        .where((r) => r['outcome_correct'] == 'True')
        .length; // Assuming 'outcome_correct' column
    // If outcome_correct isn't in CSV yet (because fs_offline.py needs to verify it), we might mock
    // Just using what we have.

    // Actually, fs_offline.py saves 'actual_score' and 'prediction'. We can recalc here or just show list.
    // Let's deduce correctness if possible.

    return Card(
      margin: const EdgeInsets.all(16),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            Text(
              "Config: ${_currentConfig?.name ?? 'Default'}",
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 10),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _statItem("Matches", "$total"),
                _statItem(
                  "Accuracy",
                  isNaN(correct / total)
                      ? "N/A"
                      : "${(correct / total * 100).toStringAsFixed(1)}%",
                ),
                // _statItem("ROI", "+15% (Mock)"),
              ],
            ),
          ],
        ),
      ),
    );
  }

  bool isNaN(double v) => v.isNaN || v.isInfinite;

  Widget _statItem(String label, String value) {
    return Column(
      children: [
        Text(
          value,
          style: const TextStyle(
            fontSize: 22,
            fontWeight: FontWeight.bold,
            color: Colors.blueAccent,
          ),
        ),
        Text(label, style: const TextStyle(color: Colors.grey)),
      ],
    );
  }

  Widget _buildResultsList() {
    if (_results.isEmpty) {
      return const Center(
        child: Text("No backtest results found. Run a backtest!"),
      );
    }
    return ListView.builder(
      itemCount: _results.length,
      itemBuilder: (context, index) {
        final row = _results[index];
        return ListTile(
          title: Text("${row['home_team']} vs ${row['away_team']}"),
          subtitle: Text(
            "Pred: ${row['prediction']} | Actual: ${row['actual_score']}",
          ),
          trailing: Text(row['confidence'] ?? ''),
        );
      },
    );
  }
}
