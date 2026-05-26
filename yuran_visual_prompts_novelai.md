# 유란 외형 일러스트 - NovelAI 프롬프트

> v1.0 - NovelAI Diffusion V4 (NAI v4) 기준
> Danbooru 태그 기반. 미드저니랑 문법 완전 다름.

---

## 0. NovelAI 핵심 사용법

### 문법 차이 (미드저니 vs NAI)

| | Midjourney | NovelAI |
|---|---|---|
| 입력 형식 | 자연어 문장 | **Danbooru 태그 (콤마 구분)** |
| 가중치 강조 | `::` 또는 `(())` | `{tag}` (1.05x) / `{{tag}}` (1.10x) |
| 가중치 감소 | `--no` 또는 `[]` | `[tag]` (1.05x 감소) |
| Negative | `--no` 파라미터 | **Undesired Content (UC) 필드** 별도 |
| 캐릭터 일관성 | `--cref [URL]` | **Vibe Transfer** (이미지 업로드) |
| 종횡비 | `--ar 2:3` | 해상도 직접 선택 (832x1216 등) |

### 권장 생성 세팅 (NAI v4)

| 항목 | 값 | 비고 |
|---|---|---|
| Model | **NAI Diffusion V4 (Curated/Full)** | Full이 더 자유도 높음 |
| Sampler | **Euler Ancestral** 또는 DPM++ 2M | Euler A가 애니에 가장 잘 맞음 |
| Steps | **28** | 23~32 사이 |
| Scale (CFG) | **5.0** | 4~6 사이. 너무 높이면 디테일 깨짐 |
| Resolution | **832 x 1216** (Portrait) | 캐릭터 풀샷용 |
| | 1024 x 1024 | 정사각 (인스타용) |
| | 1216 x 832 | 가로 (배경 컷용) |
| SMEA | **ON** | 디테일 향상 |
| SMEA DYN | ON | 추가 디테일 |
| Variety+ | OFF | 캐릭터 일관성 위해 OFF 권장 |
| Seed | Random → 베스트 시 고정 | 같은 시드 = 비슷한 결과 |

---

## 1. UC (Negative Prompt) - 모든 생성에 공통

### 베이스 UC (NAI 권장 Heavy 프리셋 + 커스텀)

```
nsfw, lowres, {bad}, error, fewer, extra, missing, worst quality, jpeg artifacts, bad quality, watermark, unfinished, displeasing, chromatic aberration, signature, extra digits, artistic error, username, scan, [abstract], bad anatomy, bad hands, multiple views, hair intakes, sexual, revealing, mature, chibi, super deformed, western style, photorealistic, 3d, smirk, evil expression, aggressive, harsh shadows, oversaturated, dark colors
```

> 캐릭터 톤 (조용함/슬픔/순수) 유지하려면 `smirk, evil, aggressive` 같은 negative 중요.

---

## 2. 캐릭터 베이스 태그 (모든 프롬프트 공통)

### 핵심 캐릭터 태그 블록 (재사용)

```
1girl, solo, slender, petite, small breasts,
long hair, lavender hair, pink hair, gradient hair, wavy hair, hair between eyes,
hair flower, white flower, small flower in hair,
green eyes, light green eyes, drooping eyes, beautiful detailed eyes,
fragile, ethereal, melancholy expression,
pale skin, soft lighting on face
```

### 핵심 의상 태그 블록

```
shrine maiden, miko outfit, ethereal dress, flower print, floral pattern,
pale cream colors, soft pink colors, layered clothes, see-through fabric,
plant bracelet, vine bracelet, barefoot
```

### 핵심 스타일 태그 (퀄리티 포함)

```
masterpiece, best quality, amazing quality, very aesthetic, absurdres, newest,
soft pastel colors, ethereal atmosphere, dreamy lighting, cinematic lighting,
detailed background, korean webtoon style, anime style, official art
```

---

## 3. 메인 비주얼 / Hero Shot ★ 최우선

### 3A. 풀샷 (캐릭터 정체성 정의)

**Prompt:**
```
1girl, solo, slender, petite, small breasts,
long hair, lavender hair, pink hair, gradient hair, wavy hair, hair between eyes,
{{hair flower}}, white flower, small flower in hair,
light green eyes, drooping eyes, {{beautiful detailed eyes}},
shrine maiden, miko outfit, ethereal dress, flower print, pale cream colors, soft pink, layered clothes,
plant bracelet, barefoot, 
holding small flower, cupped hands, 
soft melancholic smile, looking at viewer,
full body, standing, soft morning light, ethereal atmosphere,
{{masterpiece, best quality}}, very aesthetic, absurdres, soft pastel colors, dreamy lighting, korean webtoon style, official art
```

**Resolution**: 832 x 1216 (Portrait)
**용도**: 앱 메인 화면, 첫 만남 일러스트

### 3B. 어퍼바디 (앱 프로필 / 채팅 헤더)

**Prompt:**
```
1girl, solo, upper body, 
long hair, lavender hair, pink hair, gradient hair, wavy hair, hair between eyes,
{{hair flower}}, white flower,
light green eyes, drooping eyes, looking down slightly, {{beautiful detailed eyes}},
gentle melancholy expression, soft quiet smile,
shrine maiden, ethereal dress, flower print, pale cream colors,
soft window lighting, blurred warm background, indoor,
{{masterpiece, best quality}}, very aesthetic, absurdres, soft pastel colors, dreamy lighting, korean webtoon style, official art
```

**Resolution**: 832 x 1216
**용도**: 채팅 화면 헤더, 앱 아이콘 베이스

### 3C. 페이스 클로즈업 (Vibe Transfer 베이스)

**Prompt:**
```
1girl, solo, close-up, face focus,
long hair, lavender hair, pink hair, gradient hair, hair between eyes,
{{hair flower}}, white flower behind ear,
{{light green eyes}}, drooping eyes, detailed iris, {{beautiful detailed eyes}}, soft eyelashes,
gentle quiet smile, soft melancholy,
pale skin, soft natural lighting, blurred warm background,
{{masterpiece, best quality}}, amazing quality, very aesthetic, absurdres, soft pastel colors, dreamy painterly, korean webtoon style, official art, ultra detailed face
```

**Resolution**: 1024 x 1024
**용도**: ★ **Vibe Transfer 마스터 이미지** - 이걸로 모든 후속 일러스트 캐릭터 일관성 유지

---

## 4. 표정 변주 (감정 상태별 5종)

> 메인 비주얼 확정 후 **Vibe Transfer**에 3C 마스터 이미지 업로드 → 캐릭터 일관성 유지

### 4A. 조용한 미소 (디폴트)
```
[캐릭터 베이스 + 의상 베이스],
upper body, soft quiet smile, gentle warm expression, looking at viewer, peaceful, soft morning light,
[스타일 베이스]
```

### 4B. 슬픈 옆모습 (멸망 / 가족 회상)
```
[캐릭터 베이스 + 의상 베이스],
{{from side}}, profile view, looking away into distance, {{single tear}}, sad expression, melancholic, hands clasped near chest, twilight lighting, cool tones,
[스타일 베이스]
```

### 4C. 부끄러운 얼굴 (플러팅 받았을 때)
```
[캐릭터 베이스 + 의상 베이스],
upper body, {{shy}}, {{embarrassed}}, {{blush}}, looking down, half-closed eyes, fingers touching hair flower, warm pink tones, intimate close-up,
[스타일 베이스]
```

### 4D. 졸린 눈매 (자기 전 / 새벽)
```
[캐릭터 베이스 + 의상 베이스],
upper body, {{sleepy}}, half-closed eyes, {{soft yawn}}, messy hair, sitting on bed, wrapped in soft blanket, warm bedside lamp, dim lighting, intimate cozy atmosphere, night,
[스타일 베이스]
```

### 4E. 단단해지는 순간 (꽃 지킬 때)
```
[캐릭터 베이스 + 의상 베이스],
upper body, {{serious expression}}, {{determined}}, focused eyes, protective stance, {{holding flower close to chest}}, soft but resolute, slightly cool lighting,
[스타일 베이스]
```

**Resolution**: 832 x 1216 모두
**Vibe Transfer**: 마스터 페이스 클로즈업 업로드 (Information Extracted: 0.7~0.9, Reference Strength: 0.6~0.8)

---

## 5. 배경 / 환경 컷

### 5A. 본인 세계 회상 (꽃밭)
```
1girl, solo, 
[캐릭터 베이스],
ethereal shrine maiden, miko outfit, flowing dress,
standing in flower field, {{countless small wildflowers}}, fantasy landscape, magical bloom, {{sunset golden light}}, soft glowing flowers around her,
melancholic peaceful, wide shot, full body, painterly style,
{{masterpiece, best quality}}, very aesthetic, absurdres, ethereal atmosphere, dreamy lighting, korean webtoon style, official art
```

**Resolution**: 1216 x 832 (가로)

### 5B. 인간 세계 적응 (창가)
```
1girl, solo,
[캐릭터 베이스],
modern korean apartment, sitting by window, looking at small potted plant on windowsill, {{curious gentle expression}},
simple human clothes, oversized sweater, ethereal accessories,
afternoon sunlight, soft warm lighting, slice of life, cozy interior,
{{masterpiece, best quality}}, very aesthetic, absurdres, soft pastel colors, korean webtoon style, official art
```

**Resolution**: 1216 x 832

### 5C. 비 오는 날 (멜랑콜리)
```
1girl, solo,
[캐릭터 베이스],
standing on balcony, {{light rain}}, {{wet hair}}, {{raindrops}},
gazing up at gray sky, quiet sad expression, ethereal robe slightly wet,
{{soft cool colors}}, warm interior light behind, melancholic cinematic atmosphere, rainy day,
{{masterpiece, best quality}}, very aesthetic, absurdres, painterly, korean webtoon style, official art
```

**Resolution**: 832 x 1216

---

## 6. 컨셉 변주 (시즌 / 의상)

### 6A. 사복 ver (인간 세계 캐주얼)
```
1girl, solo,
[캐릭터 베이스 (의상 제외)],
{{oversized cream knit sweater}}, {{soft pleated skirt}}, modern korean street fashion, 
small flower hair accessory, holding coffee cup, casual cozy expression,
cafe interior, blurred background, slice of life,
[스타일 베이스]
```

### 6B. 룸웨어 / 자기 전
```
1girl, solo,
[캐릭터 베이스 (의상 제외)],
{{white nightgown}}, simple floral embroidery, hair loose, sitting on bed, holding small plush,
warm bedside lamp, dim cozy lighting, sleepy intimate atmosphere, night, bedroom,
[스타일 베이스]
```

### 6C. 봄 / 벚꽃
```
1girl, solo,
[캐릭터 베이스],
under cherry blossom tree, {{cherry blossoms}}, {{petals falling}}, pink sakura,
soft spring sunlight, looking up at blossoms, quiet wonder, light fluttering dress,
ethereal dreamy atmosphere, outdoors, spring,
[스타일 베이스]
```

### 6D. 여름 / 더위 적응
```
1girl, solo,
[캐릭터 베이스 (의상 제외)],
{{white sundress}}, simple summer dress, sitting on wooden floor, {{electric fan}}, hair tied up,
slightly tired sweet expression, {{summer afternoon}}, paper screen, traditional korean room, slice of life,
[스타일 베이스]
```

### 6E. 첫눈 / 겨울
```
1girl, solo,
[캐릭터 베이스 (의상 제외)],
{{first snow}}, {{snowflakes}}, snowflakes on hair, {{beige wool coat}},
looking up at sky, quiet wonder, breath visible, cold air, warm street light behind,
melancholic peaceful, winter night, outdoors,
[스타일 베이스]
```

---

## 7. 마케팅 / 인스타용 클로즈업

### 7A. 손 클로즈업 (꽃)
```
close-up, pale slender hands, {{cupping small wildflower}}, single small flower, 
{{plant bracelet}}, vine bracelet on wrist,
soft ethereal lighting, blurred lavender pink hair background, dreamy painterly,
{{masterpiece, best quality}}, amazing quality, very aesthetic, absurdres, korean webtoon style, official art, ultra detailed
```

### 7B. 머리 장식 디테일
```
extreme close-up, {{from side}}, profile, 
lavender hair, pink hair, gradient hair, {{small white flower in hair}}, hair ornament,
soft sunlight through petals, translucent flower, delicate ethereal,
{{masterpiece, best quality}}, amazing quality, very aesthetic, absurdres, painterly soft style, korean webtoon, ultra detailed
```

### 7C. 맨발 / 풀잎
```
close-up, {{bare feet}}, standing on grass, {{small wildflowers}} on ground, 
delicate ankle, hem of ethereal robe visible, soft morning dew,
painterly dreamy atmosphere, soft natural lighting,
{{masterpiece, best quality}}, amazing quality, very aesthetic, absurdres, korean webtoon style, official art
```

### 7D. 시들지 않는 꽃 (정체성 상징)
```
close-up, single small white wildflower, perfect bloom, 
{{tucked in lavender pink hair}}, soft hair strands background, 
{{sunlight through petals}}, translucent, eternally fresh,
{{masterpiece, best quality}}, amazing quality, very aesthetic, absurdres, dreamy ethereal, painterly style, ultra detailed
```

---

## 8. ★ Vibe Transfer 활용법 (캐릭터 일관성 핵심)

### 기본 워크플로우

1. **Phase 1**: 섹션 3C (페이스 클로즈업) 프롬프트로 8~12장 생성
2. 베스트 1장 선정 → **마스터 캐릭터 일러스트** 등록
3. 마스터 이미지 다운로드 → 저장

4. **Phase 2 이후**: 모든 후속 생성에서 NovelAI 우측 **"Vibe Transfer"** 활성화
   - Reference Image 업로드: 마스터 이미지
   - **Information Extracted**: 0.7~0.9 (캐릭터 특징 추출 강도)
   - **Reference Strength**: 0.6~0.8 (참조 영향력)
   - 둘 다 너무 높이면 같은 포즈/표정만 나옴. 0.7 정도가 sweet spot.

### Vibe Transfer 멀티 레퍼런스 (NAI Opus 전용)

여러 이미지 동시 참조 가능:
- Ref 1: 페이스 클로즈업 (얼굴 특징 0.8)
- Ref 2: 풀샷 (의상 특징 0.5)
- Ref 3: 표정 샘플 (감정 특징 0.6)

→ 캐릭터 핵심 유지하면서 새로운 포즈/배경 변주 가능

### 캐릭터 일관성 체크리스트
- [ ] 머리 색 (lavender pink gradient)
- [ ] 머리 길이 (long, wavy at tips)
- [ ] 머리 꽃 (white small flower)
- [ ] 눈 (light green, drooping)
- [ ] 표정 톤 (melancholy 베이스)
- [ ] 의상 컬러 (pale cream + soft pink)
- [ ] 액세서리 (plant bracelet)
- [ ] 신발 (barefoot)

---

## 9. NAI Tip / Trouble Shooting

### 자주 발생하는 문제 + 해결

| 문제 | 해결 |
|---|---|
| 캐릭터 너무 어른스러움 | `young, teenager, 18 years old` 추가 |
| 가슴이 너무 큼 | `small breasts, flat chest` 추가 + UC에 `large breasts` |
| 의상이 너무 노출 | UC에 `revealing, cleavage, midriff` 추가 |
| 얼굴이 일관되지 않음 | Vibe Transfer 강도 올림 (0.85+) |
| 손가락 이상 | UC Heavy 프리셋 + steps 32까지 올림 |
| 배경이 너무 단순 | `detailed background, intricate background` 추가 |
| 너무 칙칙함 | `{{soft pastel colors}}, {{bright}}` 강조 |
| 너무 밝음 | `[bright]` 감소 + `soft warm lighting` |

### Quality 태그 우선순위 (NAI v4 기준)

높은 효과 → 낮은 효과:
1. `masterpiece` (강력)
2. `best quality`
3. `amazing quality`
4. `very aesthetic`
5. `absurdres` (고해상도 디테일)
6. `newest` (2024+ 스타일)
7. `year 2024` 또는 `year 2025`

### 한국 웹툰 톤 강조 추가 태그
```
korean webtoon style, manhwa style, soft cell shading, gentle linework, 
official illustration, light novel style, soft watercolor
```

### 미연시/갤게 톤 강조
```
visual novel style, galge style, dating sim character art, 
soft eroge style (UC에 NSFW 필수 추가)
```

---

## 10. 진행 체크리스트

### Week 1
- [ ] NovelAI 가입 ($25 Opus 플랜 권장 - Vibe Transfer 풀 활용)
- [ ] 섹션 3C 페이스 클로즈업 8~12장 생성
- [ ] 마스터 일러스트 1장 선정 + 저장
- [ ] 섹션 3A 풀샷 + Vibe Transfer로 8장 생성
- [ ] 섹션 3B 어퍼바디 + Vibe Transfer 4장

### Week 2
- [ ] 섹션 4 표정 5종 (Vibe Transfer 활용)
- [ ] 섹션 5 배경 3종

### Week 3
- [ ] 섹션 6 컨셉 변주 5종
- [ ] 섹션 7 마케팅 클로즈업 4종

### Week 4
- [ ] 인스타 계정 개설
- [ ] 9~12장 큐레이션 → 그리드 업로드
- [ ] TTS 보이스 캐스팅 (외형 매칭)

---

## 11. NovelAI 플랜 비교

| 플랜 | 가격 | 일러스트 적합도 |
|---|---|---|
| Tablet | $10/월 | ❌ 텍스트만, 이미지 X |
| Scroll | $15/월 | ❌ 텍스트만 |
| **Opus** | **$25/월** | ✅ **무제한 이미지 + Vibe Transfer 풀 지원** ★ |

→ **반드시 Opus 결제**. Tablet/Scroll은 이미지 생성 불가.

---

## 12. 미드저니 vs NovelAI - 본인 케이스 결론

### NovelAI 강점
- ✅ **캐릭터 일관성 (Vibe Transfer)** - 미드저니 `--cref`보다 강력
- ✅ **애니/갤게 톤 정확** - 한국 demo 선호 결
- ✅ **태그 기반 정밀 제어** - 정확한 의상/포즈 지정 쉬움
- ✅ Opus $25에 무제한 - 미드저니 $30보다 가성비

### NovelAI 약점
- ❌ 자연어 못 알아듣음 - Danbooru 태그 알아야 함 (학습 필요)
- ❌ 배경 / 환경 묘사는 미드저니가 더 강함
- ❌ "폴리시드 official art" 룩은 Niji가 더 잘 뽑음

### 추천 조합 (예산 여유 있으면)
- **NovelAI Opus** ($25/월): 캐릭터 메인 양산
- **Midjourney Basic** ($10/월): 배경 / 환경 컷 / 마케팅 시네마틱
- 합 $35/월 - 두 도구 강점만 가져가기

---

*NovelAI 프롬프트 v1.0 - 작성 완료. 다음: NovelAI Opus 결제 → 섹션 3C 페이스 클로즈업으로 마스터 일러스트 확정.*
