import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../app_theme.dart';
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
  bool _englishNarrative = false;
  String _sessionLocale = 'zh';
  bool _loading = false;
  String _error = '';
  int _charm = 3;
  int _wealth = 5;
  int _reputation = 2;
  int _turn = 0;
  int _storyLength = 0;
  String _modelUsed = 'MiniMax-M2.7-highspeed';
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

  /// Pre-game: centered hero with language switch and large start CTA.
  Widget _buildHomeCenter(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        return SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24),
          child: ConstrainedBox(
            constraints: BoxConstraints(minHeight: constraints.maxHeight),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  _englishNarrative ? _enIntro : _zhIntro,
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                        color: AppColors.textSecondary,
                        height: 1.5,
                      ),
                ),
                const SizedBox(height: 32),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(
                      '中文',
                      style: TextStyle(
                        color: AppColors.contrast,
                        fontWeight: !_englishNarrative ? FontWeight.w800 : FontWeight.w500,
                      ),
                    ),
                    Switch(
                      value: _englishNarrative,
                      onChanged: _loading ? null : _onNarrativeLanguageChanged,
                      activeThumbColor: AppColors.orangeGradientEnd,
                      activeTrackColor: AppColors.orangeGradientStart.withValues(alpha: 0.5),
                    ),
                    Text(
                      'English',
                      style: TextStyle(
                        color: AppColors.contrast,
                        fontWeight: _englishNarrative ? FontWeight.w800 : FontWeight.w500,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 28),
                _GradientCtaButton(
                  onPressed: _loading ? null : _startGame,
                  label: _englishNarrative ? 'Start game' : '开始游戏',
                  minHeight: 56,
                  maxWidth: 320,
                ),
                if (_error.isNotEmpty) ...[
                  const SizedBox(height: 16),
                  Text(
                    _error,
                    textAlign: TextAlign.center,
                    style: TextStyle(color: Theme.of(context).colorScheme.error, fontSize: 13),
                  ),
                ],
                if (_loading) ...[
                  const SizedBox(height: 24),
                  const SizedBox(
                    width: 28,
                    height: 28,
                    child: CircularProgressIndicator(
                      strokeWidth: 2.5,
                      color: AppColors.orangeGradientEnd,
                    ),
                  ),
                ],
              ],
            ),
          ),
        );
      },
    );
  }

  Widget buildStoryArea(BuildContext context) {
    final ruleHints = <String>[
      '异性观测独占',
      '财力/声望准入',
      '高利益优先',
      if (_shuraMode) '修罗场博弈中',
    ];

    // 20px horizontal page margins for story + meta (after game starts this is the only path).
    const EdgeInsets scrollPadding = EdgeInsets.fromLTRB(20, 16, 20, 16);

    return SingleChildScrollView(
      controller: _scrollController,
      padding: scrollPadding,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    '本轮字数：$_storyLength | 模型：$_modelUsed',
                    style: const TextStyle(
                      fontSize: 13,
                      color: AppColors.contrast,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
                TextButton.icon(
                  onPressed: () async {
                    await Clipboard.setData(ClipboardData(text: _storyText));
                    if (!context.mounted) return;
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text(_uiEnglish ? 'Story copied.' : '剧情已复制'),
                        behavior: SnackBarBehavior.floating,
                        backgroundColor: AppColors.contrast,
                      ),
                    );
                  },
                  icon: const Icon(Icons.copy, size: 16, color: AppColors.contrast),
                  label: Text(_uiEnglish ? 'Copy' : '复制', style: const TextStyle(color: AppColors.contrast)),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              '本轮变化：魅力 ${_formatDelta(_deltaCharm)} | 财力 ${_formatDelta(_deltaWealth)} | 声望 ${_formatDelta(_deltaReputation)}',
              style: const TextStyle(
                fontSize: 13,
                color: AppColors.textSecondary,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 8),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: AppColors.card,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(
                  color: _shuraMode
                      ? AppColors.orangeGradientEnd.withValues(alpha: 0.45)
                      : AppColors.dividerSoft,
                ),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withValues(alpha: 0.05),
                    blurRadius: 12,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '状态判定：${_readableResultType(_resultType)}',
                    style: const TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w700,
                      color: AppColors.contrast,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    '成功率：${(_successRate * 100).toStringAsFixed(0)}%${_shuraMode ? "  |  修罗场模式已触发" : ""}  |  协议v$_apiSchemaVersion',
                    style: const TextStyle(
                      fontSize: 12,
                      color: AppColors.textSecondary,
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
                              color: AppColors.canvas,
                              borderRadius: BorderRadius.circular(14),
                              border: Border.all(color: AppColors.dividerSoft),
                            ),
                            child: Text(
                              e,
                              style: const TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.w600,
                                color: AppColors.contrast,
                              ),
                            ),
                          ),
                        )
                        .toList(growable: false),
                  ),
                  if (_reasonCodes.isNotEmpty) ...[
                    const SizedBox(height: 6),
                    Text(
                      '命中规则：${_reasonCodes.map(_readableReasonCode).join("，")}',
                      style: const TextStyle(
                        fontSize: 12,
                        color: AppColors.textSecondary,
                      ),
                    ),
                  ],
                ],
              ),
            ),
            const SizedBox(height: 12),
            Text(
              _storyText,
              style: const TextStyle(
                fontSize: 16,
                height: 1.6,
                color: AppColors.contrast,
              ),
            ),
          ],
        ),
      );
  }

  Widget buildChoiceArea(BuildContext context) {
    return Material(
      color: AppColors.card,
      elevation: 8,
      shadowColor: Colors.black.withValues(alpha: 0.08),
      borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
      child: Padding(
        padding: EdgeInsets.fromLTRB(
          20,
          16,
          20,
          16 + MediaQuery.of(context).padding.bottom,
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          mainAxisSize: MainAxisSize.min,
          children: [
            if (_error.isNotEmpty && _started) ...[
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
                    label: Text(
                      '${choice.id}. ${choice.text}',
                      style: TextStyle(
                        color: isSelected ? Colors.white : AppColors.contrast,
                        fontWeight: isSelected ? FontWeight.w600 : FontWeight.w500,
                      ),
                    ),
                    selected: isSelected,
                    selectedColor: AppColors.contrast,
                    backgroundColor: AppColors.canvas,
                    side: const BorderSide(color: AppColors.dividerSoft),
                    onSelected: (_) => _onChoiceTap(choice),
                  ),
                );
              }),
            const SizedBox(height: 4),
            if (_started) ...[
              FilledButton(
                style: FilledButton.styleFrom(
                  backgroundColor: AppColors.contrast,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(14),
                  ),
                ),
                onPressed: (_loading || _selectedChoiceId == null) ? null : _onConfirmTap,
                child: Text(_sessionLocale == 'en' ? 'Confirm' : '确认'),
              ),
            ],
            if (_loading && _started) ...[
              const SizedBox(height: 8),
              const Center(
                child: SizedBox(
                  width: 24,
                  height: 24,
                  child: CircularProgressIndicator(
                    strokeWidth: 2.5,
                    color: AppColors.orangeGradientEnd,
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.canvas,
      appBar: AppBar(
        toolbarHeight: 72,
        titleSpacing: 12,
        title: Row(
          children: [
            Expanded(
              child: _StatusChip(
                label: '魅力',
                value: _charm.toString(),
                icon: Icons.auto_awesome,
                accentColor: AppColors.orangeGradientEnd,
              ),
            ),
            const SizedBox(width: 6),
            Expanded(
              child: _StatusChip(
                label: '财力',
                value: _wealth.toString(),
                icon: Icons.account_balance_wallet,
                accentColor: AppColors.contrast,
              ),
            ),
            const SizedBox(width: 6),
            Expanded(
              child: _StatusChip(
                label: '声望',
                value: _reputation.toString(),
                icon: Icons.workspace_premium,
                accentColor: AppColors.contrast,
              ),
            ),
            const SizedBox(width: 6),
            Expanded(
              child: _StatusChip(
                label: '回合',
                value: _turn.toString(),
                icon: Icons.timelapse,
                accentColor: AppColors.textSecondary,
              ),
            ),
          ],
        ),
      ),
      body: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Expanded(
            child: _started ? buildStoryArea(context) : _buildHomeCenter(context),
          ),
          if (_started) buildChoiceArea(context),
        ],
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

class _GradientCtaButton extends StatelessWidget {
  const _GradientCtaButton({
    required this.onPressed,
    required this.label,
    this.minHeight = 56,
    this.maxWidth = 320,
  });

  final VoidCallback? onPressed;
  final String label;
  final double minHeight;
  final double maxWidth;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: ConstrainedBox(
        constraints: BoxConstraints(
          maxWidth: maxWidth,
          minHeight: minHeight,
          minWidth: 240,
        ),
        child: DecoratedBox(
          decoration: BoxDecoration(
            gradient: AppColors.orangeGradient,
            borderRadius: BorderRadius.circular(minHeight / 2),
            boxShadow: [
              BoxShadow(
                color: AppColors.orangeGradientEnd.withValues(alpha: 0.35),
                blurRadius: 16,
                offset: const Offset(0, 8),
              ),
            ],
          ),
          child: Material(
            type: MaterialType.transparency,
            child: InkWell(
              onTap: onPressed,
              borderRadius: BorderRadius.circular(minHeight / 2),
              child: Center(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 16),
                  child: Text(
                    label,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 18,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 0.5,
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
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
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 7),
      decoration: BoxDecoration(
        color: AppColors.card,
        border: Border.all(color: AppColors.dividerSoft),
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.04),
            blurRadius: 8,
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
                color: AppColors.contrast,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
