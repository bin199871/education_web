/**
 * Layer 1 — 题目分析 Agent
 * ============================================================
 * 混合模式：规则解析框架 + 可插拔 LLM 后端
 *
 * 流程：
 *   预处理 → 规则匹配（基线分析）→ LLM 增强（可选）→ 合并 → 最终 JSON
 *
 * 无需 LLM 也能输出完整结构（规则版）；接入 LLM 可获得更深度的语义分析。
 *
 * 使用方式：
 *   // 纯规则模式
 *   const result = analyzeProblem("题目文本...");
 *
 *   // LLM 增强模式
 *   const result = await analyzeProblem("题目文本...", {
 *     llm: { apiKey: "sk-...", model: "gpt-4o-mini" }
 *   });
 *
 *   // OpenAI 兼容接口均可，包括 Ollama 本地模型：
 *   // llm: { endpoint: "http://localhost:11434/v1/chat/completions", model: "llama3" }
 */

(function (root, factory) {
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = factory();
  } else {
    root.ProblemAnalyzer = factory();
  }
})(typeof self !== 'undefined' ? self : this, function () {

  /* ==================================================================
   *  第〇部分 — 物理知识规则库
   * ================================================================== */

  /**
   * 物理主题规则。每个主题包含：
   *   keywords       — 用于检测的关键词列表
   *   conceptName    — 核心概念名称
   *   conceptDesc    — 一句话定义
   *   keyFormula     — 核心公式
   *   variables      — 变量说明
   *   misconceptions — 常见误解
   *   sceneTemplates — 场景模板（供规则匹配使用）
   */
  var PHYSICS_TOPICS = {

    quality_gravity: {
      keywords: ['质量', '重力', '引力', 'g值', '自由落体加速度', '月球', '天平', '弹簧秤', '称重', '重量', 'G=mg'],
      conceptName: '质量与重力的区别',
      conceptDesc: '质量是物体固有属性，不随位置改变；重力是万有引力的表现，G = mg，随 g 值改变',
      keyFormula: 'G = mg',
      variables: {
        'm': { name: '质量', unit: 'kg', property: '不随位置改变，固有属性' },
        'g': { name: '重力加速度', unit: 'm/s²', property: '随星球和位置变化' },
        'G': { name: '重力', unit: 'N', property: '随 g 值变化，G=mg' }
      },
      misconceptions: [
        '质量会随重力变化（质量是固有属性，不随位置改变）',
        '失重状态下物体质量为零（失重时重力表现为零，但质量不变）',
        '质量和重量是同一概念（质量是标量，重量是力）',
        '天平在月球上读数会变（天平测质量，读数不变）'
      ],
      sceneTemplates: [
        { name: '地球表面', motion: '静止或匀速', force: '受重力 G=mg，对支持面有压力' },
        { name: '月球表面', motion: '静止或匀速', force: '受重力 G=mg/6，对支持面有压力' },
        { name: '环绕飞行', motion: '匀速圆周运动', force: '引力提供向心力，合力不为零' }
      ]
    },

    newton_law: {
      keywords: ['牛顿', '力', '加速度', 'F=ma', '惯性', '作用力', '反作用力', '合外力', '牛顿第一', '牛顿第二', '牛顿第三'],
      conceptName: '牛顿运动定律',
      conceptDesc: '牛顿三定律描述了力与运动的关系：惯性定律、F=ma、作用力与反作用力',
      keyFormula: 'F = ma',
      variables: {
        'F': { name: '合外力', unit: 'N', property: '物体所受所有力的矢量和' },
        'm': { name: '质量', unit: 'kg', property: '物体的惯性量度' },
        'a': { name: '加速度', unit: 'm/s²', property: '与合外力同向，大小正比于力' }
      },
      misconceptions: [
        '力是维持运动的原因（力是改变运动状态的原因，不是维持）',
        '质量大的物体重力加速度更大（所有物体自由落体加速度相同）',
        '作用力与反作用力相互抵消（它们作用在不同物体上）'
      ],
      sceneTemplates: [
        { name: '水平面运动', motion: '匀加速直线', force: '受推力/拉力、摩擦力、支持力、重力' },
        { name: '斜面运动', motion: '匀加速直线', force: '受重力分力、摩擦力、支持力' },
        { name: '竖直运动', motion: '匀变速直线', force: '受重力和外力（若有）' }
      ]
    },

    circular_motion: {
      keywords: ['圆周', '向心', '离心', '匀速圆周', '轨道', '环绕', '角速度', '线速度', '周期', 'F=mv²/r'],
      conceptName: '匀速圆周运动',
      conceptDesc: '物体沿圆周运动，速度大小不变、方向不断改变，需要向心力维持',
      keyFormula: 'F = mv²/r = mω²r',
      variables: {
        'F': { name: '向心力', unit: 'N', property: '指向圆心，不是独立力而是合力效果' },
        'v': { name: '线速度', unit: 'm/s', property: '沿切线方向，大小不变' },
        'ω': { name: '角速度', unit: 'rad/s', property: '单位时间转过的角度' },
        'r': { name: '半径', unit: 'm', property: '圆周轨道半径' }
      },
      misconceptions: [
        '匀速圆周运动合力为零（合力提供向心力，不为零）',
        '向心力是独立力（向心力是效果力，由其他力提供）',
        '圆周运动速度不变（速度方向不断变化）'
      ],
      sceneTemplates: [
        { name: '水平转弯', motion: '匀速圆周运动', force: '摩擦力或支持力分力提供向心力' },
        { name: '竖直圆周', motion: '变速圆周运动', force: '重力与支持力的合力提供向心力' },
        { name: '卫星轨道', motion: '匀速圆周运动', force: '万有引力提供向心力' }
      ]
    },

    energy: {
      keywords: ['能量', '功', '功率', '动能', '势能', '机械能', '守恒', '动能定理', 'W=Fs', 'Ep=mgh', 'Ek=mv²/2'],
      conceptName: '能量与功',
      conceptDesc: '功是能量转化的量度，机械能包括动能和势能，在只有保守力做功时机械能守恒',
      keyFormula: 'W = ΔEk = Fs·cosθ',
      variables: {
        'W': { name: '功', unit: 'J', property: '力在位移方向上的累积效应' },
        'Ek': { name: '动能', unit: 'J', property: 'Ek = ½mv²，与速度平方成正比' },
        'Ep': { name: '势能', unit: 'J', property: '重力势能 Ep = mgh' },
        'P': { name: '功率', unit: 'W', property: 'P = W/t = Fv' }
      },
      misconceptions: [
        '有力就一定有做功（需要有位移，且力与位移不垂直）',
        '机械能守恒时动能不变（动能和势能可以相互转化）',
        '功率越大做功越多（功 = 功率×时间）'
      ],
      sceneTemplates: [
        { name: '自由落体', motion: '匀加速直线', force: '重力做功，势能转化为动能' },
        { name: '斜面滑下', motion: '匀加速直线', force: '重力分力做功，可能有摩擦生热' },
        { name: '竖直上抛', motion: '匀减速到最高点', force: '重力做功，动能转化为势能' }
      ]
    },

    electricity: {
      keywords: ['电流', '电压', '电阻', '电路', '欧姆', '串联', '并联', '电荷', 'I=U/R', '电功率', 'P=UI'],
      conceptName: '欧姆定律与电路',
      conceptDesc: '通过导体的电流与导体两端电压成正比，与导体电阻成反比',
      keyFormula: 'I = U/R',
      variables: {
        'I': { name: '电流', unit: 'A', property: '电荷定向移动形成，串联处处相等' },
        'U': { name: '电压', unit: 'V', property: '电路两端的电势差' },
        'R': { name: '电阻', unit: 'Ω', property: '导体固有属性，与电压电流无关' }
      },
      misconceptions: [
        '电阻大小由电压和电流决定（R=U/I是计算式，电阻是导体属性）',
        '电流从正极流到负极消耗完了（串联电流处处相等）',
        '短路时电流极大（正确，但需区分电源短路和局部短路）'
      ],
      sceneTemplates: [
        { name: '串联电路', motion: '—', force: '电流处处相等，电压之和等于总电压' },
        { name: '并联电路', motion: '—', force: '电压相等，电流之和等于干路电流' },
        { name: '混联电路', motion: '—', force: '先串后并或先并后串，逐级分析' }
      ]
    },

    momentum: {
      keywords: ['动量', '冲量', '碰撞', '守恒', 'Ft=mv', '弹性碰撞', '非弹性碰撞', '动量定理'],
      conceptName: '动量与碰撞',
      conceptDesc: '动量是物体运动量的量度，系统不受外力时动量守恒',
      keyFormula: 'p = mv, Ft = Δp',
      variables: {
        'p': { name: '动量', unit: 'kg·m/s', property: '矢量，方向与速度相同' },
        'I': { name: '冲量', unit: 'N·s', property: '力对时间的累积效应，矢量' },
        'v': { name: '速度', unit: 'm/s', property: '碰撞前后速度变化' }
      },
      misconceptions: [
        '动量守恒时动能也守恒（只有弹性碰撞动能守恒）',
        '质量大的物体动量一定大（动量 p=mv，还与速度有关）',
        '碰撞后物体都停止运动（需要满足动量守恒条件）'
      ],
      sceneTemplates: [
        { name: '一维碰撞', motion: '匀速直线（碰撞前后）', force: '碰撞内力远大于外力' },
        { name: '爆炸/反冲', motion: '向相反方向运动', force: '内力作用，系统动量守恒' }
      ]
    }

  };

  /* ==================================================================
   *  第一部分 — 文本解析引擎（规则驱动）
   * ================================================================== */

  var TextParser = {

    /**
     * 将原始题目文本解析为结构化片段。
     * 支持常见选择题格式：
     *   "题干... A. 选项A B. 选项B C. 选项C D. 选项D"
     *   "题干... A、选项A B、选项B ……"
     *
     * @param {string} rawText
     * @returns {{ stem: string, options: Array<{label:string,text:string}> }}
     */
    parse: function (rawText) {
      if (!rawText || typeof rawText !== 'string') {
        return { stem: '', options: [] };
      }

      var text = rawText.trim();

      // 尝试匹配选项标签：A. / A、 / A) / A． （全角点）
      var optionRegex = /([A-Da-d])[.、)）．\s]\s*/g;
      var matches = [];
      var match;

      while ((match = optionRegex.exec(text)) !== null) {
        matches.push({ label: match[1].toUpperCase(), index: match.index });
      }

      // 如果找到了 4 个选项
      var options = [];
      var stem = text;

      if (matches.length >= 4) {
        // 取前 4 个以 A,B,C,D 顺序出现的选项
        var abcd = matches.filter(function (m, i) {
          var expectedLabel = String.fromCharCode(65 + i); // A,B,C,D
          return m.label === expectedLabel && i < 4;
        });

        if (abcd.length >= 2) {
          // 题干 = 文本开始到第一个选项之前
          stem = text.slice(0, abcd[0].index).trim();

          for (var i = 0; i < abcd.length; i++) {
            var start = abcd[i].index;
            // 选项文本从标签之后开始
            var labelEnd = start + (abcd[i].label.length + 1); // skip "A."
            while (labelEnd < text.length && text[labelEnd] === ' ') labelEnd++;

            var end;
            if (i + 1 < abcd.length) {
              end = abcd[i + 1].index;
            } else {
              end = text.length;
            }

            var optText = text.slice(labelEnd, end).trim();
            // 去除末尾可能的标点
            optText = optText.replace(/[；;。，,]+$/, '').trim();

            options.push({ label: abcd[i].label, text: optText });
          }
        }
      }

      // 清理题干中的 "下列说法正确的是" 等前缀
      stem = stem.replace(/^[①②③④⑤]?[\s]*/, '').trim();

      return { stem: stem, options: options };
    },

    /**
     * 从题干中提取关键条件（数字、单位、物理量）。
     * @param {string} text
     * @returns {string[]}
     */
    extractConditions: function (text) {
      var conditions = [];
      // 匹配数值+单位的模式
      var numUnitRegex = /(\d+\.?\d*)\s*(m\/s²|m\/s|m|kg|N|J|W|V|A|Ω|s|h|km|g|cm|mm)/g;
      var m;
      while ((m = numUnitRegex.exec(text)) !== null) {
        conditions.push(m[0].trim());
      }
      return conditions;
    }
  };

  /* ==================================================================
   *  第二部分 — 规则分析引擎
   * ================================================================== */

  var RuleEngine = {

    /**
     * 检测题目涉及哪些物理主题。
     * 返回按匹配关键词数量排序的主题 ID 列表。
     */
    detectTopics: function (text) {
      var scores = [];
      var allText = text;

      for (var topicId in PHYSICS_TOPICS) {
        var topic = PHYSICS_TOPICS[topicId];
        var matchCount = 0;
        var matchedKeywords = [];

        for (var ki = 0; ki < topic.keywords.length; ki++) {
          var kw = topic.keywords[ki];
          if (allText.indexOf(kw) !== -1) {
            matchCount++;
            matchedKeywords.push(kw);
          }
        }

        if (matchCount > 0) {
          scores.push({
            topicId: topicId,
            score: matchCount,
            matchedKeywords: matchedKeywords
          });
        }
      }

      scores.sort(function (a, b) { return b.score - a.score; });
      return scores;
    },

    /**
     * 基于检测到的主题生成核心概念 JSON。
     */
    buildCoreConcept: function (topicId) {
      var topic = PHYSICS_TOPICS[topicId];
      if (!topic) return null;

      return {
        name: topic.conceptName,
        definition: topic.conceptDesc,
        key_formula: topic.keyFormula,
        variables: JSON.parse(JSON.stringify(topic.variables)),
        common_misconceptions: topic.misconceptions.slice()
      };
    },

    /**
     * 基于题目文本和检测到的主题，生成场景分析。
     */
    analyzeScenario: function (text, topicId) {
      var topic = PHYSICS_TOPICS[topicId];
      var scenes = [];

      if (topic && topic.sceneTemplates) {
        for (var si = 0; si < topic.sceneTemplates.length; si++) {
          var tmpl = topic.sceneTemplates[si];
          // 检查题干中是否提及该场景的关键词
          var sceneKeywords = tmpl.name.split('');
          var matched = false;
          for (var ki = 0; ki < sceneKeywords.length; ki++) {
            if (text.indexOf(sceneKeywords[ki]) !== -1) {
              matched = true;
              break;
            }
          }
          // 某些场景即使没有显式关键词也加入（默认场景）
          scenes.push({
            name: tmpl.name,
            motion: tmpl.motion,
            force: tmpl.force
          });
        }
      }

      // 提取已知条件
      var conditions = TextParser.extractConditions(text);

      return {
        context: text.length > 80 ? text.slice(0, 80) + '…' : text,
        key_conditions: conditions.length > 0 ? conditions.join('；') : '需进一步分析',
        scenes: scenes
      };
    },

    /**
     * 对选项进行初步分析（规则版基本分析）。
     * 规则版无法判断对错，返回中性分析。
     */
    analyzeOptions: function (options) {
      return options.map(function (opt) {
        return {
          label: opt.label,
          statement: opt.text,
          correct: false,     // 规则版无法判断，默认 false
          reason: '需 LLM 或人工判断'
        };
      });
    },

    /**
     * 从选项文本中猜测正确答案的描述（尝试看是否开头有 ✓/✅/正确 等标记）。
     * 主要用于测试场景。
     */
    guessAnswerFromMarkers: function (options, fullText) {
      for (var i = 0; i < options.length; i++) {
        var optText = options[i].text;
        // 检查选项开头是否有特殊标记
        if (/^[✅✔✓○●]/.test(optText)) {
          return options[i].label;
        }
      }
      return '';
    }
  };

  /* ==================================================================
   *  第三部分 — LLM 接口
   * ================================================================== */

  var LLMClient = {

    /**
     * 构建发送给 LLM 的 prompt。
     * 包含完整的题目信息和目标 JSON 结构。
     */
    buildPrompt: function (parsedText, topicHints) {
      var optionsText = parsedText.options.map(function (o) {
        return o.label + '. ' + o.text;
      }).join('\n');

      var hintText = '';
      if (topicHints && topicHints.length > 0) {
        hintText = '（提示：该题可能涉及 "' +
          topicHints.map(function (t) {
            var topic = PHYSICS_TOPICS[t.topicId];
            return topic ? topic.conceptName : t.topicId;
          }).join('、') + '"）';
      }

      return [
        {
          role: 'system',
          content: '你是一个物理题目分析专家。你需要分析一道物理选择题，输出结构化的 JSON 分析结果。\n\n' +
            '输出必须严格遵循以下 JSON 格式（不加 markdown 代码块标记，直接输出纯 JSON）：\n' +
            JSON.stringify({
              topic: '知识点名称（如"质量与重力辨析"）',
              subject: '物理',
              question_type: '选择题',
              core_concept: {
                name: '核心概念名称',
                definition: '概念定义（一句话）',
                key_formula: '核心公式',
                variables: {
                  '变量名如 m': { name: '中文名', unit: '单位', property: '关键属性说明' }
                },
                common_misconceptions: ['常见误解1（含澄清）', '常见误解2']
              },
              scenario_analysis: {
                context: '题目背景情境描述（一句话概括）',
                key_conditions: '关键已知条件',
                scenes: [
                  { name: '场景名', motion: '运动状态', force: '受力情况' }
                ]
              },
              options_analysis: [
                { label: 'A', statement: '选项原文', correct: false, reason: '判断理由' }
              ],
              answer: '正确的选项字母（如 A/B/C/D）'
            }, null, 2)
        },
        {
          role: 'user',
          content: '请分析以下物理选择题：\n\n【题干】\n' + parsedText.stem +
            '\n\n【选项】\n' + optionsText +
            (hintText ? '\n\n' + hintText : '') +
            '\n\n请严格按照上述 JSON 格式输出分析结果。'
        }
      ];
    },

    /**
     * 调用 LLM API（兼容 OpenAI Chat Completion 格式）。
     *
     * @param {Array} messages - [{ role, content }]
     * @param {object} llmConfig - { apiKey, endpoint, model }
     * @returns {Promise<string>} LLM 返回的文本
     */
    call: async function (messages, llmConfig) {
      if (!llmConfig || !llmConfig.apiKey) {
        throw new Error('LLM 未配置：缺少 apiKey');
      }

      var endpoint = llmConfig.endpoint || 'https://api.openai.com/v1/chat/completions';
      var model = llmConfig.model || 'gpt-4o-mini';
      var maxTokens = llmConfig.maxTokens || 4096;
      var temperature = llmConfig.temperature !== undefined ? llmConfig.temperature : 0.1;

      var response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + llmConfig.apiKey
        },
        body: JSON.stringify({
          model: model,
          messages: messages,
          max_tokens: maxTokens,
          temperature: temperature
        })
      });

      if (!response.ok) {
        var errorBody = '';
        try { errorBody = await response.text(); } catch (e) {}
        throw new Error('LLM API 错误 (' + response.status + '): ' + errorBody);
      }

      var data = await response.json();
      if (!data.choices || data.choices.length === 0) {
        throw new Error('LLM 返回结果为空');
      }

      return data.choices[0].message.content || '';
    },

    /**
     * 解析 LLM 返回的 JSON 文本，兼容可能包含 markdown 代码块标记的情况。
     */
    parseResponse: function (content) {
      if (!content) return null;

      var jsonStr = content;

      // 去掉可能的 markdown 代码块标记 ```json ... ```
      var jsonMatch = jsonStr.match(/```(?:json)?\s*([\s\S]*?)```/);
      if (jsonMatch) {
        jsonStr = jsonMatch[1].trim();
      }

      try {
        return JSON.parse(jsonStr);
      } catch (e) {
        // 尝试提取最外层 { } 内的内容
        var braceMatch = jsonStr.match(/\{[\s\S]*\}/);
        if (braceMatch) {
          try {
            return JSON.parse(braceMatch[0]);
          } catch (e2) {}
        }
        throw new Error('无法解析 LLM 返回的 JSON: ' + jsonStr.slice(0, 200));
      }
    }
  };

  /* ==================================================================
   *  第四部分 — 结果合并器
   * ================================================================== */

  var ResultMerger = {

    /**
     * 将规则分析结果和 LLM 分析结果合并。
     * 规则结果为基线，LLM 结果补充增强，同时做完整性校验。
     *
     * @param {object} ruleResult  - 规则引擎的输出
     * @param {object|null} llmResult - LLM 的输出（可能为空）
     * @param {object} parsedText  - 文本解析结果
     * @returns {object} 最终标准 JSON
     */
    merge: function (ruleResult, llmResult, parsedText) {
      // 以规则结果为基线
      var finalResult = JSON.parse(JSON.stringify(ruleResult));

      if (llmResult) {
        // 用 LLM 结果覆盖/补充
        if (llmResult.topic) finalResult.topic = llmResult.topic;
        if (llmResult.subject) finalResult.subject = llmResult.subject;

        // 核心概念 — 优先用 LLM 的详细版本
        if (llmResult.core_concept) {
          var mergedConcept = JSON.parse(JSON.stringify(finalResult.core_concept || {}));
          if (llmResult.core_concept.name) mergedConcept.name = llmResult.core_concept.name;
          if (llmResult.core_concept.definition) mergedConcept.definition = llmResult.core_concept.definition;
          if (llmResult.core_concept.key_formula) mergedConcept.key_formula = llmResult.core_concept.key_formula;
          if (llmResult.core_concept.variables) {
            // 合并变量，LLM 的变量覆盖同名变量
            for (var vk in llmResult.core_concept.variables) {
              if (llmResult.core_concept.variables.hasOwnProperty(vk)) {
                mergedConcept.variables[vk] = llmResult.core_concept.variables[vk];
              }
            }
          }
          if (llmResult.core_concept.common_misconceptions &&
              llmResult.core_concept.common_misconceptions.length > 0) {
            mergedConcept.common_misconceptions = llmResult.core_concept.common_misconceptions;
          }
          finalResult.core_concept = mergedConcept;
        }

        // 场景分析
        if (llmResult.scenario_analysis) {
          var mergedScenario = JSON.parse(JSON.stringify(finalResult.scenario_analysis || {}));
          if (llmResult.scenario_analysis.context) mergedScenario.context = llmResult.scenario_analysis.context;
          if (llmResult.scenario_analysis.key_conditions) mergedScenario.key_conditions = llmResult.scenario_analysis.key_conditions;
          if (llmResult.scenario_analysis.scenes && llmResult.scenario_analysis.scenes.length > 0) {
            mergedScenario.scenes = llmResult.scenario_analysis.scenes;
          }
          finalResult.scenario_analysis = mergedScenario;
        }

        // 选项分析 — 用 LLM 的（包含对错判断）
        if (llmResult.options_analysis && llmResult.options_analysis.length > 0) {
          finalResult.options_analysis = llmResult.options_analysis;
        }

        // 答案
        if (llmResult.answer) finalResult.answer = llmResult.answer;
      }

      // 补齐字段（确保结构完整）
      finalResult = this._ensureComplete(finalResult, parsedText);
      return finalResult;
    },

    /**
     * 确保输出结构的完整性和一致性。
     */
    _ensureComplete: function (result, parsedText) {
      // 确保必有字段
      result.topic = result.topic || '未识别的物理主题';
      result.subject = result.subject || '物理';
      result.question_type = result.question_type || '选择题';

      // 核心概念
      if (!result.core_concept) {
        result.core_concept = {
          name: '待分析',
          definition: '需进一步分析',
          key_formula: '',
          variables: {},
          common_misconceptions: []
        };
      }
      if (!result.core_concept.variables) result.core_concept.variables = {};
      if (!result.core_concept.common_misconceptions) result.core_concept.common_misconceptions = [];

      // 场景分析
      if (!result.scenario_analysis) {
        result.scenario_analysis = {
          context: parsedText.stem.slice(0, 80) + (parsedText.stem.length > 80 ? '…' : ''),
          key_conditions: '',
          scenes: []
        };
      }
      if (!result.scenario_analysis.scenes) result.scenario_analysis.scenes = [];

      // 选项分析
      if (!result.options_analysis || result.options_analysis.length === 0) {
        result.options_analysis = parsedText.options.map(function (o) {
          return {
            label: o.label,
            statement: o.text,
            correct: false,
            reason: '待分析'
          };
        });
      }

      // 答案
      result.answer = result.answer || '';

      return result;
    }
  };

  /* ==================================================================
   *  第五部分 — 主入口
   * ================================================================== */

  /**
   * 分析一道物理题目。
   *
   * @param {string} text - 原始题目文本
   * @param {object} [options] - 配置选项
   * @param {object} [options.llm] - LLM 配置（不提供则纯规则模式）
   * @param {string} [options.llm.apiKey] - API 密钥
   * @param {string} [options.llm.endpoint] - API 端点（默认 OpenAI）
   * @param {string} [options.llm.model] - 模型名（默认 gpt-4o-mini）
   * @param {number} [options.llm.maxTokens] - 最大输出 token 数
   * @param {number} [options.llm.temperature] - 温度参数
   * @param {string} [options.forceTopic] - 强制指定主题 ID（调试用）
   * @param {boolean} [options.verbose] - 是否输出详细日志
   * @returns {Promise<object>} 结构化分析结果
   *
   * @example
   *   // 纯规则模式
   *   var result = analyzeProblem("题干... A. 选项A ...");
   *
   *   // LLM 增强模式
   *   var result = await analyzeProblem(text, {
   *     llm: { apiKey: "sk-xxx", model: "gpt-4o-mini" }
   *   });
   */
  async function analyzeProblem(text, options) {
    options = options || {};
    var verbose = options.verbose || false;

    if (verbose) console.log('[Layer1] 开始分析题目…');

    // ---- 第1步：文本解析 ----
    var parsed = TextParser.parse(text);
    if (verbose) {
      console.log('[Layer1] 文本解析完成：', parsed);
    }

    if (!parsed.stem) {
      throw new Error('无法解析题目文本，请检查格式（需要包含题干和 A/B/C/D 选项）');
    }

    // ---- 第2步：规则分析 ----
    var detectedTopics = RuleEngine.detectTopics(text);
    var primaryTopicId = options.forceTopic ||
      (detectedTopics.length > 0 ? detectedTopics[0].topicId : null);

    if (verbose) {
      console.log('[Layer1] 检测到的主题：', detectedTopics);
      console.log('[Layer1] 主要主题：', primaryTopicId);
    }

    var ruleResult = {
      topic: primaryTopicId ? PHYSICS_TOPICS[primaryTopicId].conceptName : '未识别的物理主题',
      subject: '物理',
      question_type: '选择题',
      core_concept: primaryTopicId ? RuleEngine.buildCoreConcept(primaryTopicId) : {
        name: '待分析',
        definition: '需进一步分析',
        key_formula: '',
        variables: {},
        common_misconceptions: []
      },
      scenario_analysis: primaryTopicId
        ? RuleEngine.analyzeScenario(text, primaryTopicId)
        : { context: parsed.stem.slice(0, 80), key_conditions: '', scenes: [] },
      options_analysis: RuleEngine.analyzeOptions(parsed.options),
      answer: RuleEngine.guessAnswerFromMarkers(parsed.options, text)
    };

    // ---- 第3步：LLM 增强（可选） ----
    var llmResult = null;
    if (options.llm && options.llm.apiKey) {
      if (verbose) console.log('[Layer1] 调用 LLM 进行深度分析…');

      try {
        var messages = LLMClient.buildPrompt(parsed, detectedTopics);
        var llmResponse = await LLMClient.call(messages, options.llm);
        llmResult = LLMClient.parseResponse(llmResponse);

        if (verbose) {
          console.log('[Layer1] LLM 分析完成：', llmResult);
        }

        // 验证 LLM 返回了完整的选项分析
        if (llmResult && llmResult.options_analysis) {
          var llmLabels = llmResult.options_analysis.map(function (o) { return o.label; });
          var parsedLabels = parsed.options.map(function (o) { return o.label; });
          var match = llmLabels.length === parsedLabels.length &&
            llmLabels.every(function (l, i) { return l === parsedLabels[i]; });

          if (!match) {
            if (verbose) console.warn('[Layer1] LLM 选项标签不匹配，回退到规则结果');
            llmResult.options_analysis = null;
          }
        }
      } catch (llmErr) {
        if (verbose) console.warn('[Layer1] LLM 分析失败：', llmErr.message);
        // LLM 失败不回滚，继续使用规则结果
      }
    }

    // ---- 第4步：合并结果 ----
    var finalResult = ResultMerger.merge(ruleResult, llmResult, parsed);

    if (verbose) {
      console.log('[Layer1] 最终分析结果：');
      console.log(JSON.stringify(finalResult, null, 2));
    }

    return finalResult;
  }

  /**
   * 获取支持的物理主题列表。
   */
  function getSupportedTopics() {
    var topics = [];
    for (var id in PHYSICS_TOPICS) {
      if (PHYSICS_TOPICS.hasOwnProperty(id)) {
        topics.push({
          id: id,
          name: PHYSICS_TOPICS[id].conceptName,
          keywords: PHYSICS_TOPICS[id].keywords
        });
      }
    }
    return topics;
  }

  /* ==================================================================
   *  导出
   * ================================================================== */

  return {
    analyzeProblem: analyzeProblem,
    getSupportedTopics: getSupportedTopics,
    // 内部模块也暴露，方便调试
    TextParser: TextParser,
    RuleEngine: RuleEngine,
    LLMClient: LLMClient,
    ResultMerger: ResultMerger,
    PHYSICS_TOPICS: PHYSICS_TOPICS
  };

});
