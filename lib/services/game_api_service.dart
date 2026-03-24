import 'dart:convert';

import 'package:http/http.dart' as http;

class GameChoice {
  const GameChoice({
    required this.id,
    required this.text,
  });

  final String id;
  final String text;
}

class GameApiResponse {
  const GameApiResponse({
    required this.storyText,
    required this.choices,
    required this.charm,
    required this.wealth,
    required this.reputation,
    required this.turn,
    required this.storyLength,
    required this.modelUsed,
    required this.deltaCharm,
    required this.deltaWealth,
    required this.deltaReputation,
    required this.resultType,
    required this.reasonCodes,
    required this.successRate,
    required this.shuraMode,
    required this.apiSchemaVersion,
  });

  final String storyText;
  final List<GameChoice> choices;
  final int charm;
  final int wealth;
  final int reputation;
  final int turn;
  final int storyLength;
  final String modelUsed;
  final int deltaCharm;
  final int deltaWealth;
  final int deltaReputation;
  final String resultType;
  final List<String> reasonCodes;
  final double successRate;
  final bool shuraMode;
  final String apiSchemaVersion;
}

class GameApiService {
  GameApiService({
    http.Client? client,
    String? baseUrl,
  })  : _client = client ?? http.Client(),
        baseUrl = baseUrl ??
            const String.fromEnvironment(
              'GAME_API_BASE_URL',
              defaultValue: 'http://127.0.0.1:8000',
            );

  final http.Client _client;
  final String baseUrl;

  Future<GameApiResponse> startGame() async {
    final uri = Uri.parse('$baseUrl/start');
    final response = await _client.post(
      uri,
      headers: const {'Content-Type': 'application/json'},
      body: '{}',
    );
    return _parseResponse(response);
  }

  Future<GameApiResponse> playTurn(String choice) async {
    final uri = Uri.parse('$baseUrl/play');
    final response = await _client.post(
      uri,
      headers: const {'Content-Type': 'application/json'},
      body: jsonEncode({'choice': choice}),
    );
    return _parseResponse(response);
  }

  GameApiResponse _parseResponse(http.Response response) {
    if (response.statusCode != 200) {
      throw Exception('Request failed: ${response.statusCode} ${response.body}');
    }

    final decoded = jsonDecode(response.body) as Map<String, dynamic>;
    final storyText = (decoded['story_text'] ?? decoded['story'] ?? '').toString();
    final attributes = (decoded['attributes'] as Map<String, dynamic>? ?? const <String, dynamic>{});
    final charm = (attributes['charm'] as num?)?.toInt() ?? 0;
    final wealth = (attributes['wealth'] as num?)?.toInt() ?? 0;
    final reputation = (attributes['reputation'] as num?)?.toInt() ?? 0;
    final turn = (decoded['turn'] as num?)?.toInt() ?? 0;
    final storyLength = (decoded['story_length'] as num?)?.toInt() ?? storyText.length;
    final modelUsed = (decoded['model_used'] ?? 'unknown').toString();
    final stateDelta = (decoded['state_delta'] as Map<String, dynamic>? ?? const <String, dynamic>{});
    final deltaCharm = (stateDelta['charm'] as num?)?.toInt() ?? 0;
    final deltaWealth = (stateDelta['wealth'] as num?)?.toInt() ?? 0;
    final deltaReputation = (stateDelta['reputation'] as num?)?.toInt() ?? 0;
    final resultType = (decoded['result_type'] ?? 'unknown').toString();
    final rawReasonCodes = (decoded['reason_codes'] as List<dynamic>? ?? const <dynamic>[]);
    final reasonCodes = rawReasonCodes.map((e) => e.toString()).toList(growable: false);
    final successRate = (decoded['success_rate'] as num?)?.toDouble() ?? 0;
    final shuraMode = decoded['shura_mode'] == true;
    final apiSchemaVersion = (decoded['api_schema_version'] ?? '1.0').toString();
    final rawChoices = (decoded['choices'] as List<dynamic>? ?? const <dynamic>[]);
    final choices = rawChoices.map((item) {
      if (item is Map<String, dynamic>) {
        final id = (item['id'] ?? '').toString();
        final text = (item['text'] ?? id).toString();
        return GameChoice(id: id, text: text);
      }
      final value = item.toString();
      return GameChoice(id: value, text: value);
    }).toList(growable: false);

    if (storyText.isEmpty || choices.length < 3) {
      throw Exception('Invalid backend response: ${response.body}');
    }

    return GameApiResponse(
      storyText: storyText,
      choices: choices.take(3).toList(growable: false),
      charm: charm,
      wealth: wealth,
      reputation: reputation,
      turn: turn,
      storyLength: storyLength,
      modelUsed: modelUsed,
      deltaCharm: deltaCharm,
      deltaWealth: deltaWealth,
      deltaReputation: deltaReputation,
      resultType: resultType,
      reasonCodes: reasonCodes,
      successRate: successRate,
      shuraMode: shuraMode,
      apiSchemaVersion: apiSchemaVersion,
    );
  }
}
