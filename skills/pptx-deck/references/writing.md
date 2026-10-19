# Writing — words, sentence form, notation

Text on a slide is **a sentence the presenter would read aloud to the people who
decide**. It is not a memo or a chat message, so choose words and sentence
forms deliberately. Organization-specific voice, terminology, and required
disclaimers belong in [`../brand/guidelines.md`](../brand/guidelines.md) and
override the defaults here.

---

## 1. Sentence form — fix one form per position

Mixed sentence forms in one deck read as rushed work. Decide per position:

| Position | Form | Example |
|---|---|---|
| **Headline** | A complete declarative sentence, or a crisp result phrase | "Every request passes through only three tiers" · "All 8 workstreams in progress" |
| **Lead / prose** | Complete sentences | "Each stage moves to the next only when its exit criteria are met." |
| **Bullets, card body** | One consistent form per slide: all sentence fragments starting with a verb, or all noun phrases | "Guarantees tenant isolation by configuration" |
| **Table cells, chips, labels** | Noun phrases, no period | "Technical review" · "$12.4k / month" |
| **Captions, sources** | Noun phrases | "Internal measurement, 2026-07" |
| **Speaker notes** | Spoken sentences | "Here we close the deck and move to discussion." |

### Avoid

- **Telegraphic memo style** ("Supported.", "Done – needs check") in headlines or leads.
- **Imperative instructions to the audience** ("Must confirm", "To do") unless the slide is an action list.
- **Different forms bullet by bullet on one slide.** Pick one.
- **Unanswered questions.** A question headline is fine only when the page
  answers it in one sentence directly below (`lead_style: band`), and only for
  real research, survey, workshop or decision questions — never rhetorical ones.
  Count the questions left for the body to answer, not the questions: that
  number should be zero. Never use a question on a recommendation page.
- **Exclamation marks.** Never.

### Headlines state the conclusion as a full sentence

If the headline is a topic label, the audience must read the whole body to learn
the point. If it is the conclusion, the headline alone carries it. Its length
follows the delivery mode ([composition.md](composition.md) §1): one line when
presented, up to two lines (about 25 words, one sentence) when read.

- "Architecture overview" (label) → "Every request passes through only three tiers" (conclusion)
- "Cost analysis" (label) → "Consolidating the databases cuts monthly cost by 61%" (conclusion)

Read the headlines top to bottom; the story must flow
([composition.md](composition.md), horizontal logic).

The topic (section name, continuation marker) belongs in the eyebrow. A sub-lead
under the headline must not repeat it; it adds one reason or condition the
headline could not hold. Every number in a headline must trace to the exhibit's
data or a stated calculation. Layer roles: [reader-craft.md](reader-craft.md) §1.

---

## 2. Register — match the audience

Decision makers and practitioners read the same slides. No slang, no colloquial
intensifiers, no words that cheapen the offer.

| Do not write | Write | Why |
|---|---|---|
| cheap | cost-effective · lower unit cost | "Cheap" implies low quality |
| expensive | higher unit cost · significant cost burden | |
| money | cost · budget · investment | |
| developers like it | developer productivity rises | Turn opinion into an outcome |
| good / bad | suitable / not suitable | Make the criterion visible |
| really, super, insanely fast | (delete) or a number | "p99 200 ms" instead of "really fast" |
| always · never | in most cases · typically | Avoid absolutes that have counterexamples |
| obviously · of course | (delete) | The audience may not know |
| grunt work | manual work · repetitive work | |
| it blows up · it dies | an outage occurs · service stops | |

### No hype, no unsupported superlatives

- "Industry-leading", "revolutionary", "game-changer", "unmatched" — unsupported
  superlatives erode trust.
- Speak in numbers with sources: "Median build time 4 min vs 11 min (internal
  measurement, 2026-07)" instead of "the most reliable".
- Prefer the user's own wording over marketing copy.

### Competitors and other companies

- Use the official company and product names. No nicknames or disparaging terms.
- When stating a weakness, state facts only; no emotional modifiers.
- Check the external-distribution classification of any competitive comparison.

### Customers and people

- Use customer names and person names **only with confirmed permission**;
  otherwise describe the type ("a national telecom operator").
- Use official job titles.
- Never put real names in example data.

---

## 3. Notation

| Item | Rule | Example |
|---|---|---|
| Proper nouns | As officially written; no ad-hoc abbreviations | Kubernetes · PostgreSQL |
| Product names | Official form; first mention in full | "Order Service (OS)" then "OS" |
| Numbers | Thousands separators | 1,240 · 3,480 h |
| Units | Consistent within the deck | 200 ms · 12 GB · $4.8k / month |
| Percent | Attached to the number | 61% |
| Ranges | En dash | 2026-06–08 · 3–5 days |
| Dates | ISO or one written style, consistent | 2026-07-15 · July 15, 2026 |
| Before → after | Arrow | 24 days → 5 days |
| Inline lists | Middle dot or commas, consistent | Design · Validate · Deploy |
| Emphasis | Bold only. No underline, italics, or colored text for emphasis | |
| Periods | Complete sentences only; never on noun phrases or table cells | |
| Parentheses | Original term or a short gloss only; never nested | Recovery Point Objective (RPO) |
| Same unit form | One spelling per deck | "3x" or "3 times", not both |

---

## 4. No emoji

Do not put 🟢 🚀 ✅ ⚠️ 💡 or any other emoji on a slide. The reasons are not taste:

1. **Rendering differs by OS and application.** Presenter and audience see different glyphs and colors.
2. **PDF export and printing break them** or turn them monochrome.
3. **They bring colors from outside the brand tokens**, breaking the one-or-two-accent rule.
4. **They lighten the tone** and cost credibility in front of decision makers.

Use instead:

| Intended with emoji | Use |
|---|---|
| 🟢 🟡 🔴 status | A status dot in `colors.positive` / `colors.warning` / `colors.negative` **plus a text label** |
| ✅ done · ❌ unsupported | The words "Done" (bold if it is the focus) · "Not supported", or a check / cross icon from the approved set |
| 🚀 📈 speed, growth | A number plus a before → after delta, or a chart |
| ⚠️ caution | A callout box, or a warning status label |
| 💡 tip | A quiet `colors.surface_alt` band or callout |
| 🔒 🔗 ⚙️ concepts, components | An icon from the approved icon set (below) |

Circled numerals (①②③) may serve as list numbers, for example in a table's
first column, when the layout has no built-in numbering.

Treat any emoji found during QA as an error, not a warning.

### Icons

- Use icons **only from the brand icon set** (`icons.path` in `brand.yaml`, searched
  with `python scripts/find_icon.py <keyword>`) **or a permissively licensed
  generic icon set the organization approves.** Nothing else.
- Never guess a file path; use the path the search returns.
- Do not recolor, distort, or redraw official product or partner icons; keep them
  square and label them with the exact product name.
- Do not mix styles within a set (for example outline and solid); weights become uneven.
- **Add an icon only when it explains something.** An icon that points at nothing is noise.

---

## 5. For Korean-language decks

### Sentence endings — one per position

| 자리 | 어미 | 예 |
|---|---|---|
| 헤드라인 | 명사형 결론구 (기본) 또는 해라체 `~다` | "검토 요청의 절반이 하루 이상 대기" · "요청은 세 계층만 통과한다" |
| 리드문 | `~합니다` | "각 단계는 명확한 완료기준으로 다음 단계로 넘어갑니다." |
| 불릿 · 카드 본문 | 명사형 종결 또는 `~한다` (한 장 안에서 통일) | "테넌트별 격리를 구성으로 보장" · "릴리스마다 같은 점검을 사람이 반복한다" |
| 표 셀 · 칩 · 라벨 | 명사구, 마침표 없음 | "기술검토" · "월 1,240만원" |
| 캡션 · 출처 | 명사구 | "2026-07 내부 실측" |
| 발표자 노트 | `~합니다` (실제 발화) | "여기서 자료를 덮고 대화로 넘어갑니다." |

- **헤드라인은 결론구로 끝낸다.** 명사형 결론구("~ 확산", "~ 달성", "~는 강화")나
  `~다`로 끝내고, `~합니다`는 리드문과 노트에 쓴다. 헤드라인이 `~습니다` `~합니다`로 끝나면 lint가
  INFO로 알린다. 조직이 헤드라인에도 `~합니다`를 쓰기로 했다면 `brand/guidelines.md`에
  적고 그대로 둔다. "주제 – 결론"처럼 en dash로 이어도 된다("검토 대기 – 리드타임의 절반 차지").
- **메모체 금지**: `~함` `~됨` `~임`. "지원함" (X) → "지원합니다" 또는 "지원" (O)
- **지시서 말투 금지**: `~해야함` `~할것`. "확정해야 합니다" 또는 "확정" (O)
- 한 슬라이드 안에서 불릿마다 어미가 다르면 하나로 통일한다.
- 느낌표는 쓰지 않는다. 질문형 제목은 바로 아래 한 문장 답(`lead_style: band`)이 있을 때만 쓴다.

### Register — words to replace

| 쓰지 않는다 | 쓴다 |
|---|---|
| 싼 · 저렴한 | 비용 효율적인 · 낮은 단가의 |
| 비싼 | 단가가 높은 · 비용 부담이 큰 |
| 댓가 | 대가 (이 자리에는 보통 "비용"이 맞다) |
| 돈 | 비용 · 예산 · 투자 |
| 깎다 · 후려치다 | 절감하다 · 조정하다 |
| 개발자들이 편함 | 개발 생산성이 올라갑니다 |
| 엄청 · 되게 · 진짜 | (지운다) 또는 수치 |
| 대박 · 짱 · 개~ | (쓰지 않는다) |
| ~해버리다 · ~치우다 | ~합니다 |
| 무조건 · 절대 | 대부분 · 통상 |
| 당연히 | (지운다) |
| 어쩔 수 없이 | 제약 때문에 |
| 노가다 · 삽질 | 수작업 · 반복 작업 |
| 죽는다 · 터진다 | 장애가 발생합니다 · 중단됩니다 |
| 갑 · 을 | 발주사 · 수행사 (또는 실제 회사명) |

### Notation

- 단위는 숫자에 붙여 쓴다: 200ms · 12GB · 월 480만원.
- 퍼센트포인트 변화는 `%p`: "3.2%p 상승". 한 덱에서 `%포인트`와 섞지 않는다(lint WARN).
- 차트·표의 단위는 오른쪽 위 괄호 라벨로: "(단위: %)", "(단위: 억원, 전년 대비)",
  "(2026년 1월=100)". 이중 축은 "(좌)" "(우)".
- 기간은 물결표: 2026-06~08 · 2026~27년. 분기는 "2/4분기" 또는 "2분기" 중 하나로 통일한다.
- 나열은 가운뎃점: 설계 · 검증 · 배포. 개수를 앞세우는 제목은 "5대 과제"처럼 쓸 수 있다.
- 출처 접두어는 한 덱에 하나: `자료:` 또는 `출처:`. 브랜드의 `copy.source_label`에 한 번
  정하고 `source`에는 접두어 없이 내용만 쓴다. 주석은 `주:` (출처 위에 둔다). 접두어가 섞이면
  lint가 WARN을 낸다.
- 이어지는 장은 "(계속)" 또는 "(1/2)" "(2/2)"를 eyebrow나 헤드라인 끝에 붙인다. 한 덱에서 한 방식만 쓴다.
- 한·영 병기는 원문 검색·대조가 필요한 용어에만: 첫 등장 `한국어(English)`. 제품명은 공식 영문 그대로.

---

## 6. Self-check

1. One sentence form per position (headline, lead, bullets, tables)?
2. Any telegraphic memo style left (Korean: `~함` `~됨` `~해야함`)?
3. Any unsupported superlative or hype?
4. Any slang or colloquialism?
5. Any emoji at all?
6. Are customer and person names approved for use?
7. Does every number carry a unit and a source? One source prefix per deck?
8. Question headlines: is each one answered directly below?
9. **Do the headlines alone tell the story?**
