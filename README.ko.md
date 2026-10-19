# pptx-deck-skill

[English](README.md) · **버전 0.2.0** · [변경 내역](CHANGELOG.md) · [릴리스](https://github.com/jeonghun-app/pptx-deck-skill/releases)

발표 내용을 **우리 조직의 디자인을 따르는, 편집 가능한 PowerPoint 파일**로 만들어 주는
에이전트 스킬입니다. 이야기의 구조는 모델이 잡고, 색·글꼴·위치·슬라이드 패턴은
브랜드 프로필이 정합니다.

- **`pptx-deck`**: PLAN → BUILD → QA 순서로 진행합니다. 청중·목적·최종 문구를 담은
  계획 파일(`deck.yaml`)을 python-pptx로 PPTX로 만들고, 컨택트시트로 렌더링해 점검합니다.
- **`pptx-layout-audit`**: 어떤 PPTX든 정렬·간격·연결선·최소 글자 크기·대비·편집
  가능성을 덱 전체에 걸쳐 검토합니다.

![예제 덱, 기본(중립) 브랜드](docs/images/sample-neutral-contact.png)

슬라이드 원본 크기 이미지와 PPTX 파일은 [예제](#예제)에서 볼 수 있습니다.

## 0.2에서 달라진 점

- **요점을 스스로 말하는 도표**
  - 구조화된 각주(주석, 질문, 대상, n, 기준일, 출처)
  - 강조색 하나와 회색 배경 색
  - 선 끝 라벨, `waterfall`, 추정치 표시
  - 데이터에서 계산한 주석(기준선, 구간, 콜아웃, 증감)
  - 도표 옆 `commentary` 해설 열, 작은 차트 묶음 `panels`
- **프레임워크 레이아웃**
  - `matrix`(2×2/3×3)
  - 기호 표(하비볼, 체크, 상태)
  - `shift`(현재 → 목표)
  - 정렬된 행이 붙은 셰브론 `process`
  - 번호를 단 열린 `cards`, 최대 9개 값의 `stats` 격자
- **읽는 구조**
  - 장별 결론으로 만든 요약(`summary`)과 진행 표시
  - 두 줄 제목을 쓰는 읽기 모드
  - 질문형 제목의 답변 띠, `next_steps` 띠
- **추정 대신 측정**: 실제로 렌더링되는 글꼴로 글자 폭을 재기 때문에 줄바꿈·넘침 경고가 슬라이드와 일치합니다.
- **한국어 관례**: 명사형 제목, `%p`, 단위·출처 표기를 지원합니다.

0.1에서 업그레이드하는 경우, 기존 계획 파일과 브랜드 파일은 그대로 빌드됩니다. 눈에 보이게 바뀐 기본값이 몇 가지 있습니다.

- 꺾은선 끝 라벨
- 본문 한 줄 길이 상한
- 기본 팔레트를 쓸 때 여러 계열에 강조색 단계 적용

각 항목을 끄는 방법은 [변경 내역](CHANGELOG.md)에 있습니다.

## 왜 만들었나

모델이 만든 슬라이드는 대개 티가 납니다. 제각각인 색, 전부 굵은 글씨, 모든 생각을
카드로 만든 구성, 넘치는 글자가 그렇습니다. 이 스킬은 두 가지 일을 나눕니다.

- **이야기와 제작법**은 스킬이 맡습니다. 결론형 제목, 한 장 한 메시지, 표·차트·도식
  선택, 밀도 한계, 연결선의 의미, 글쓰기 규칙, QA가 여기에 속합니다.
- **디자인**은 *여러분의* 파일이 맡습니다. `brand/brand.yaml`에는 토큰과 회사
  템플릿을, `brand/guidelines.md`에는 문체·용어·승인된 패턴·예외를 적습니다. 이 두
  파일만 바꾸면 같은 덱이 다른 브랜드로 다시 만들어집니다.

결과물은 PowerPoint 네이티브 파일입니다. 텍스트 상자는 그대로 편집할 수 있고, 표와
차트는 데이터가 포함된 네이티브 개체입니다. 도식은 연결선이 붙은 도형으로 그려지고,
모든 장에 발표자 노트가 들어갑니다.

## 예제

아래 덱은 모두 [`skills/pptx-deck/examples/decks/`](skills/pptx-deck/examples/decks)의
계획 파일을 생성기로 빌드한 결과이며, 손으로 고친 부분이 없습니다. PPTX를 내려받아
PowerPoint, Keynote 또는 Google Slides에서 열면 모든 요소를 편집할 수 있는지 확인할 수
있습니다. GitHub는 PPTX를 미리 보여주지 않으므로 아래 이미지는 같은 파일을
LibreOffice로 렌더링한 것입니다.

### 1. 한국어 덱과 사용자 지정 슬라이드

[⬇ ko-sample.pptx](docs/examples/ko-sample.pptx) · 계획 파일:
[`ko-sample.deck.yaml`](skills/pptx-deck/examples/decks/ko-sample.deck.yaml) · 간트 차트는
deckkit 함수로 작성한 `custom` 슬라이드입니다
([`custom/gantt.py`](skills/pptx-deck/examples/decks/custom/gantt.py)).

| | |
|---|---|
| ![표지](docs/images/slides/ko-sample-01.png) | ![숫자](docs/images/slides/ko-sample-02.png) |
| ![카드](docs/images/slides/ko-sample-03.png) | ![간트](docs/images/slides/ko-sample-04.png) |

### 2. 제안 덱(기본 브랜드)

[⬇ sample-neutral.pptx](docs/examples/sample-neutral.pptx) · 계획 파일:
[`sample.deck.yaml`](skills/pptx-deck/examples/decks/sample.deck.yaml) · 19장

| | |
|---|---|
| ![표지](docs/images/slides/sample-neutral-01.png) | ![요약](docs/images/slides/sample-neutral-03.png) |
| `cover` | `summary`: 장마다 결론 한 묶음, 요청은 하단 띠에 |
| ![숫자](docs/images/slides/sample-neutral-05.png) | ![차트](docs/images/slides/sample-neutral-06.png) |
| `stats`: 출처를 함께 표시한 숫자 | `chart`: 네이티브 차트에서 막대 하나를 강조하고 옆에 해석을 둡니다 |
| ![도식](docs/images/slides/sample-neutral-10.png) | ![표](docs/images/slides/sample-neutral-11.png) |
| `diagram`: 네이티브 도형, 붙어 있는 연결선, 경계 | `table`: 권장 열을 강조합니다 |
| ![이미지](docs/images/slides/sample-neutral-15.png) | ![카드](docs/images/slides/sample-neutral-16.png) |
| `image`: 캡션과 대체 텍스트가 있는 화면 이미지 | `cards`: 한 장을 강조합니다 |

<details>
<summary>19장 전체 보기</summary>

![컨택트시트](docs/images/sample-neutral-contact.png)

</details>

### 3. 같은 덱, 다른 브랜드 프로필

[⬇ sample-warm-editorial.pptx](docs/examples/sample-warm-editorial.pptx) · 브랜드:
[`warm-editorial/brand.yaml`](skills/pptx-deck/examples/brands/warm-editorial/brand.yaml).
약 40줄로 색, 세리프 제목 글꼴, 둥근 패널, 제목 밑줄 없음, 푸터 문구를 바꿨습니다.
계획 파일은 그대로입니다.

| | |
|---|---|
| ![표지](docs/images/slides/sample-warm-editorial-01.png) | ![도식](docs/images/slides/sample-warm-editorial-10.png) |
| ![표](docs/images/slides/sample-warm-editorial-11.png) | ![마무리](docs/images/slides/sample-warm-editorial-19.png) |

<details>
<summary>19장 전체 보기</summary>

![컨택트시트](docs/images/sample-warm-editorial-contact.png)

</details>

### 4. 도표: 요점을 스스로 말하는 차트

[⬇ exhibits.pptx](docs/examples/exhibits.pptx) · 계획 파일:
[`exhibits.deck.yaml`](skills/pptx-deck/examples/decks/exhibits.deck.yaml)

| | |
|---|---|
| ![각주](docs/images/slides/exhibits-05.png) | ![끝 라벨](docs/images/slides/exhibits-10.png) |
| 구조화된 각주: 주석 → 질문 · 대상 · n · 기준일 → 출처 | 선 끝 라벨, 기준선, 추정치는 점선과 표기로 구분 |
| ![워터폴](docs/images/slides/exhibits-11.png) | ![증감](docs/images/slides/exhibits-12.png) |
| `waterfall`과 옆 해설 열 | 증감 값은 데이터에서 계산하고 손으로 쓰지 않습니다 |
| ![패널](docs/images/slides/exhibits-14.png) | ![해설](docs/images/slides/exhibits-18.png) |
| `panels`: 같은 축과 기준선의 작은 차트 묶음 | 도식 옆 `commentary` |

### 5. 프레임워크: 한 장에서 끝나는 판단

[⬇ frameworks.pptx](docs/examples/frameworks.pptx) · 계획 파일:
[`frameworks.deck.yaml`](skills/pptx-deck/examples/decks/frameworks.deck.yaml)

| | |
|---|---|
| ![매트릭스](docs/images/slides/frameworks-05.png) | ![기호 표](docs/images/slides/frameworks-09.png) |
| `matrix`: 사분면 이름, 양 축의 양끝, 배치 근거 표시 | 기호 표: 하비볼, 범례, "해당 없음"을 따로 표시 |
| ![전환](docs/images/slides/frameworks-13.png) | ![셰브론](docs/images/slides/frameworks-15.png) |
| `shift`: 현재 → 목표, 한 행에 한 항목 | `process` 셰브론과 정렬된 행, "현재" 표시 |
| ![번호 열](docs/images/slides/frameworks-18.png) | ![숫자 격자](docs/images/slides/frameworks-21.png) |
| 번호를 단 열린 열로 쓰는 권고 | 최대 9개 값의 `stats` 격자 |

### 6. 스토리: 읽는 덱

[⬇ story.pptx](docs/examples/story.pptx) · 계획 파일:
[`story.deck.yaml`](skills/pptx-deck/examples/decks/story.deck.yaml) · `meta.mode: read`
(고정된 영역에 두 줄 제목)와 점 진행 표시

| | |
|---|---|
| ![요약](docs/images/slides/story-02.png) | ![진행 표시](docs/images/slides/story-05.png) |
| 장별 결론으로 만든 요약 페이지 | 진행 표시, `eyebrow: auto`, 한 줄 길이 상한 |
| ![답변 띠](docs/images/slides/story-06.png) | ![다음 단계](docs/images/slides/story-09.png) |
| 질문형 제목과 바로 아래 답변 띠 | 논지를 마무리하는 `next_steps` 띠 |

레이아웃이나 브랜드를 바꾼 뒤에는 `./build-examples.sh`로 예제를 다시 만듭니다.

## 설치

Python 3.11 이상이 필요합니다. 시각 QA를 하려면 LibreOffice(`soffice`)와
Poppler(`pdftoppm`)도 설치합니다.

**Claude Code 플러그인으로 설치**

```
/plugin marketplace add jeonghun-app/pptx-deck-skill
/plugin install pptx-deck@pptx-deck-skill
```

설치 후 `pip install -r requirements.txt`로 Python 의존성을 설치합니다.

**스킬 폴더로 직접 설치**(Claude Code 또는 `SKILL.md` 폴더를 읽는 다른 에이전트)

```
git clone https://github.com/jeonghun-app/pptx-deck-skill
cd pptx-deck-skill && ./install.sh      # ~/.claude/skills에 링크하고 의존성 설치
```

## 우리 회사 디자인으로 바꾸기

1. **회사 템플릿에서 시작하기**(권장)

   ```
   cd skills/pptx-deck
   python scripts/extract_brand.py ~/company-template.pptx -o brand/brand.yaml --report brand/extract-report.md
   ```

   템플릿이 `brand/assets/`로 복사되고, 템플릿의 레이아웃이 표지·간지·본문·마무리·빈 화면에
   하나씩 연결됩니다. 이후 덱은 이 템플릿의 마스터 위에 만들어지므로 배경·로고·제목
   스타일은 템플릿을 따릅니다. 어떤 테마 색이 강조색인지는 스크립트가 알 수 없으니
   보고서를 보고 직접 확인합니다.

2. **처음부터 만들기**: `skills/pptx-deck/brand/brand.yaml`을 고칩니다. 일부 값만
   적어도 됩니다. 적지 않은 값은 기본값을 그대로 씁니다
   (예: `examples/brands/warm-editorial/brand.yaml`).

   빌드하는 컴퓨터에 브랜드 글꼴이 설치되어 있지 않으면 `fonts.<role>.file`에
   글꼴 파일 경로를 지정합니다. 그래야 글자 폭을 정확히 잴 수 있습니다.
   `colors.series`를 직접 정한 브랜드는 그 차트 팔레트를 그대로 씁니다.

3. **숫자가 아닌 규칙 적기**: 문체, 쓰지 않는 단어, 꼭 넣어야 하는 장, 승인된 패턴,
   도식 규칙을 `brand/guidelines.md`에 적습니다.

4. **확인하기**: 내 브랜드로 예제 덱을 빌드하고 컨택트시트를 봅니다.

   ```
   python scripts/build_deck.py examples/decks/sample.deck.yaml -o out/sample.pptx
   python scripts/render_deck.py out/sample.pptx      # out/sample.render/contact.png
   ```

여러 규칙이 충돌하면 이 순서로 따릅니다. 대화에서 명시한 요청 > 회사 템플릿과
`brand.yaml` > `guidelines.md` > 스킬 기본값.

## 사용법

에이전트에게 덱을 요청합니다(예: "○○ 제안서 10장 만들어 줘"). 스킬은 이렇게 진행합니다.

1. 근거 자료를 요청하고, 추론할 수 없는 것을 묻습니다(청중, 목적, 원하는 행동, 분량).
2. `<이름>.deck.yaml`을 작성하고 사용자 승인을 기다립니다.
3. 빌드·검사·렌더링을 하고, 모든 장을 직접 확인해 고친 뒤 무엇을 점검했는지 보고합니다.

직접 실행할 수도 있습니다.

```
cd skills/pptx-deck
python scripts/lint_deck.py my.deck.yaml
python scripts/build_deck.py my.deck.yaml -o out/my.pptx
python scripts/render_deck.py out/my.pptx
python ../pptx-layout-audit/scripts/deck-craft-lint.py out/my.pptx --brand brand/brand.yaml
```

덱 전체 옵션은 `meta`에 씁니다. 자세한 내용은
[`references/deck-format.md`](skills/pptx-deck/references/deck-format.md)를 봅니다.

- `mode: read`: 미리 읽는 덱. 고정된 영역에 두 줄 제목을 씁니다.
- `tracker: tabs | dots`: 진행 표시
- `language: ko`: 한국어 문구

레이아웃: `cover`, `section`, `agenda`, `summary`, `statement`, `bullets`,
`two_column`, `cards`, `stats`, `table`, `chart`(`waterfall`, `panels` 포함),
`matrix`, `shift`, `process`, `timeline`, `diagram`, `quote`, `image`, `code`,
`closing`, `custom`. `custom`은 브랜드가 연결된 그리기 함수로 직접
작성하는 Python 렌더러입니다. 자세한 내용은
[`references/layouts.md`](skills/pptx-deck/references/layouts.md)를 봅니다.

한국어 덱은 `meta.language: ko`로 지정합니다. 한국어 문장 규칙(자리별 종결어미,
메모체 금지 등)은 [`references/writing.md`](skills/pptx-deck/references/writing.md)에
있습니다.

## 저장소 구조

```
skills/
  pptx-deck/
    SKILL.md              에이전트가 따르는 작업 순서
    brand/                우리 조직의 디자인: brand.yaml, guidelines.md, assets/
    references/           제작법: 구성, 글쓰기, 시각화, 도식, 데이터, QA
    scripts/              build_deck, render_deck, lint_deck, extract_brand, find_icon, deckkit/
    examples/             예제 덱과 예제 브랜드
  pptx-layout-audit/
    SKILL.md, references/, scripts/ (inspect-layout, deck-craft-lint)
docs/                     예제 PPTX 파일과 렌더링 미리보기 (./build-examples.sh)
```

## 테스트

```
pip install -r requirements.txt
python -m pytest skills/pptx-deck/scripts/tests
python -B skills/pptx-layout-audit/scripts/test_inspect_layout.py
python -B skills/pptx-layout-audit/scripts/test_deck_craft_lint.py
```

## 참고

- 시각 QA에 쓰는 LibreOffice 렌더링은 PowerPoint와 완전히 같지 않습니다. 렌더링하는
  컴퓨터에 브랜드 글꼴을 설치하고, 최종 파일은 청중이 쓰는 프로그램에서 열어 확인합니다.
- 로고·글꼴·아이콘·이미지는 조직에 사용 권한이 있는 것만 씁니다. 이 저장소에는
  그런 자산이 포함되어 있지 않습니다.

## 라이선스

MIT
