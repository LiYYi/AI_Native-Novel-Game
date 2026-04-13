import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../services/game_api_service.dart';

class SimpleGamePage extends StatefulWidget {
  const SimpleGamePage({super.key});

  @override
  State<SimpleGamePage> createState() => _SimpleGamePageState();
}

class _SimpleGamePageState extends State<SimpleGamePage> {
  static const _zhIntro = '点击“开始游戏”生成初始剧情。';
  static const _enIntro = 'Tap “Start game” to generate the opening scene.';

  final GameApiService _api = GameApiService();
  final ScrollController _scrollController = ScrollController();

  String _storyText = _zhIntro;
  List<GameChoice> _choices = const [];
  String? _selectedChoiceId;
  bool _started = false;
  /// Narrative language for the next `startGame` call (before game starts).
  bool _englishNarrative = false;
  /// Locale from server after start (`zh` / `en`); used for in-game UI strings.
  String _sessionLocale = 'zh';
  bool _loading = false;
  String _error = '';
  int _charm = 3;
  int _wealth = 5;
  int _reputation = 2;
  int _turn = 0;
  int _storyLength = 0;
  String _modelUsed = 'MiniMax-M2.7';
  int _deltaCharm = 0;
  int _deltaWealth = 0;
  int _deltaReputation = 0;
  String _resultType = 'start';
  List<String> _reasonCodes = const [];
  double _successRate = 1.0;
  bool _shuraMode = false;
  String _apiSchemaVersion = '1.0';

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  bool get _uiEnglish => _started ? (_sessionLocale == 'en') : _englishNarrative;

  void _onNarrativeLanguageChanged(bool english) {
    setState(() {
      _englishNarrative = english;
      if (!_started) {
        _storyText = english ? _enIntro : _zhIntro;
      }
    });
  }

  Future<void> _startGame() async {
    setState(() {
      _loading = true;
      _error = '';
    });
    try {
      final result = await _api.startGame(
        narrativeLocale: _englishNarrative ? 'en' : 'zh',
      );
      setState(() {
        _started = true;
        _sessionLocale = result.locale;
        _storyText = result.storyText;
        _choices = result.choices;
        _selectedChoiceId = null;
        _charm = result.charm;
        _wealth = result.wealth;
        _reputation = result.reputation;
        _turn = result.turn;
        _storyLength = result.storyLength;
        _modelUsed = result.modelUsed;
        _deltaCharm = result.deltaCharm;
        _deltaWealth = result.deltaWealth;
        _deltaReputation = result.deltaReputation;
        _resultType = result.resultType;
        _reasonCodes = result.reasonCodes;
        _successRate = result.successRate;
        _shuraMode = result.shuraMode;
        _apiSchemaVersion = result.apiSchemaVersion;
      });
      _scrollToBottom();
    } catch (e) {
      setState(() {
        _error = e.toString();
      });
    } finally {
      if (mounted) {
        setState(() {
          _loading = false;
        });
      }
    }
  }

  void _onChoiceTap(GameChoice choice) {
    if (_loading || !_started) return;
    setState(() {
      _selectedChoiceId = choice.id;
    });
  }

  Future<void> _onConfirmTap() async {
    if (_selectedChoiceId == null || _loading || !_started) return;
    final selectedChoice = _choices.firstWhere(
      (c) => c.id == _selectedChoiceId,
      orElse: () => _choices.first,
    );

    setState(() {
      _loading = true;
      _error = '';
      // Append player choice immediately for stronger feedback.
      final choseLabel = _sessionLocale == 'en' ? 'You chose:' : '你选择了：';
      _storyText = '$_storyText\n\n$choseLabel ${selectedChoice.id}. ${selectedChoice.text}';
      _selectedChoiceId = null;
    });
    _scrollToBottom();

    final storyAfterChoice = _storyText;
    try {
      final result = await _api.playTurn(selectedChoice.id);
      if (!mounted) return;
      setState(() {
        _storyText = '$storyAfterChoice\n\n${result.storyText}';
        _choices = result.choices.take(3).toList(growable: false);
        _charm = result.charm;
        _wealth = result.wealth;
        _reputation = result.reputation;
        _turn = result.turn;
        _storyLength = result.storyLength;
        _modelUsed = result.modelUsed;
        _deltaCharm = result.deltaCharm;
        _deltaWealth = result.deltaWealth;
        _deltaReputation = result.deltaReputation;
        _resultType = result.resultType;
        _reasonCodes = result.reasonCodes;
        _successRate = result.successRate;
        _shuraMode = result.shuraMode;
        _apiSchemaVersion = result.apiSchemaVersion;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString();
        _storyText = storyAfterChoice;
      });
    } finally {
      if (mounted) {
        setState(() {
          _loading = false;
        });
      }
    }
    _scrollToBottom();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_scrollController.hasClients) return;
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent,
        duration: const Duration(milliseconds: 280),
        curve: Curves.easeOut,
      );
    });
  }

  Widget buildStoryArea(BuildContext context) {
    final ruleHints = <String>[
      '异性观测独占',
      '财力/声望准入',
      '高利益优先',
      if (_shuraMode) '修罗场博弈中',
    ];

    return Expanded(
      child: SingleChildScrollView(
        controller: _scrollController,
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    '本轮字数：$_storyLength | 模型：$_modelUsed',
                    style: TextStyle(
                      fontSize: 13,
                      color: Theme.of(context).colorScheme.primary,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
                TextButton.icon(
                  onPressed: () async {
                    await Clipboard.setData(ClipboardData(text: _storyText));
                    if (!mounted) return;
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text(_uiEnglish ? 'Story copied.' : '剧情已复制'),
                      ),
                    );
                  },
                  icon: const Icon(Icons.copy, size: 16),
                  label: Text(_uiEnglish ? 'Copy' : '复制'),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              '本轮变化：魅力 ${_formatDelta(_deltaCharm)} | 财力 ${_formatDelta(_deltaWealth)} | 声望 ${_formatDelta(_deltaReputation)}',
              style: TextStyle(
                fontSize: 13,
                color: Theme.of(context).colorScheme.secondary,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 8),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.surfaceContainerHighest,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(
                  color: _shuraMode
                      ? Colors.deepOrange.withValues(alpha: 0.5)
                      : Theme.of(context).colorScheme.outlineVariant,
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '状态判定：${_readableResultType(_resultType)}',
                    style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    '成功率：${(_successRate * 100).toStringAsFixed(0)}%${_shuraMode ? "  |  修罗场模式已触发" : ""}  |  协议v$_apiSchemaVersion',
                    style: TextStyle(
                      fontSize: 12,
                      color: Theme.of(context).colorScheme.onSurfaceVariant,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Wrap(
                    spacing: 6,
                    runSpacing: 6,
                    children: ruleHints
                        .map(
                          (e) => Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                            decoration: BoxDecoration(
                              color: Theme.of(context).colorScheme.surface,
                              borderRadius: BorderRadius.circular(14),
                            ),
                            child: Text(
                              e,
                              style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600),
                            ),
                          ),
                        )
                        .toList(growable: false),
                  ),
                  if (_reasonCodes.isNotEmpty) ...[
                    const SizedBox(height: 6),
                    Text(
                      '命中规则：${_reasonCodes.map(_readableReasonCode).join("，")}',
                      style: TextStyle(
                        fontSize: 12,
                        color: Theme.of(context).colorScheme.onSurfaceVariant,
                      ),
                    ),
                  ],
                ],
              ),
            ),
            const SizedBox(height: 8),
            Text(
              _storyText,
              style: const TextStyle(fontSize: 16, height: 1.6),
            ),
          ],
        ),
      ),
    );
  }

  Widget buildChoiceArea(BuildContext context) {
    return Container(
      color: Colors.grey.shade200,
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        mainAxisSize: MainAxisSize.min,
        children: [
          if (_error.isNotEmpty) ...[
            Text(
              _error,
              style: TextStyle(color: Theme.of(context).colorScheme.error),
            ),
            const SizedBox(height: 8),
          ],
          if (_started)
            ..._choices.map((choice) {
              final isSelected = _selectedChoiceId == choice.id;
              return Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: ChoiceChip(
                  label: Text('${choice.id}. ${choice.text}'),
                  selected: isSelected,
                  onSelected: (_) => _onChoiceTap(choice),
                ),
              );
            }),
          const SizedBox(height: 4),
          if (!_started) ...[
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  '中文',
                  style: TextStyle(
                    fontWeight: !_englishNarrative ? FontWeight.w800 : FontWeight.w400,
                  ),
                ),
                Switch(
                  value: _englishNarrative,
                  onChanged: _loading ? null : _onNarrativeLanguageChanged,
                ),
                Text(
                  'English',
                  style: TextStyle(
                    fontWeight: _englishNarrative ? FontWeight.w800 : FontWeight.w400,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            FilledButton(
              onPressed: _loading ? null : _startGame,
              child: Text(_englishNarrative ? 'Start game' : '开始游戏'),
            ),
          ] else ...[
            FilledButton(
              onPressed: (_loading || _selectedChoiceId == null) ? null : _onConfirmTap,
              child: Text(_sessionLocale == 'en' ? 'Confirm' : '确认'),
            ),
          ],
          if (_loading) ...[
            const SizedBox(height: 8),
            const Center(child: CircularProgressIndicator()),
          ],
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        toolbarHeight: 72,
        elevation: 0,
        backgroundColor: Theme.of(context).colorScheme.surface,
        titleSpacing: 12,
        title: Row(
          children: [
            Expanded(
              child: _StatusChip(
                label: '魅力',
                value: _charm.toString(),
                icon: Icons.auto_awesome,
                accentColor: Colors.purple,
              ),
            ),
            const SizedBox(width: 6),
            Expanded(
              child: _StatusChip(
                label: '财力',
                value: _wealth.toString(),
                icon: Icons.account_balance_wallet,
                accentColor: Colors.amber.shade800,
              ),
            ),
            const SizedBox(width: 6),
            Expanded(
              child: _StatusChip(
                label: '声望',
                value: _reputation.toString(),
                icon: Icons.workspace_premium,
                accentColor: Colors.teal,
              ),
            ),
            const SizedBox(width: 6),
            Expanded(
              child: _StatusChip(
                label: '回合',
                value: _turn.toString(),
                icon: Icons.timelapse,
                accentColor: Colors.blueGrey,
              ),
            ),
          ],
        ),
      ),
      body: Padding(
        padding: EdgeInsets.zero,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            buildStoryArea(context),
            buildChoiceArea(context),
          ],
        ),
      ),
    );
  }

  String _formatDelta(int value) {
    if (value > 0) return '+$value';
    return '$value';
  }

  String _readableResultType(String type) {
    switch (type) {
      case 'success':
        return '成功推进';
      case 'partial_success':
        return '部分成功';
      case 'blocked':
        return '受阻失败';
      case 'start':
        return '开局阶段';
      default:
        return type;
    }
  }

  String _readableReasonCode(String code) {
    switch (code) {
      case 'GAME_START':
        return '章节开局';
      case 'WEALTH_GATE_FAIL':
        return '财力准入不足';
      case 'POWER_PRESSURE_SUCCESS':
        return '硬核压制奏效';
      case 'EMOTIONAL_INFLUENCE_SUCCESS':
        return '心理策略奏效';
      case 'TACTICAL_OBSERVATION':
        return '战术观察收益';
      default:
        return code;
    }
  }
}

class _StatusChip extends StatelessWidget {
  const _StatusChip({
    required this.label,
    required this.value,
    required this.icon,
    required this.accentColor,
  });

  final String label;
  final String value;
  final IconData icon;
  final Color accentColor;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 7),
      decoration: BoxDecoration(
        color: colorScheme.surfaceContainerHighest,
        border: Border.all(color: accentColor.withValues(alpha: 0.35)),
        borderRadius: BorderRadius.circular(10),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.06),
            blurRadius: 6,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        children: [
          Icon(icon, size: 14, color: accentColor),
          const SizedBox(width: 5),
          Expanded(
            child: Text(
              '$label $value',
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
