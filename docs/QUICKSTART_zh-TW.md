# ISL 對外版快速開始（P2）

ISL 是獨立的低門檻光譜數值語言研究原型，採用 MIT 授權。安裝 Python 3.10+，不需要連線或其他模型，就能執行 `.isl 0.1` 的基本運算。

```bash
python -m spectral_public.cli run examples/hello.isl
python -m unittest discover -s tests -v
```

P2 額外提供「第三方編碼器」的標準交換資料：模型在外部依文字及語境提供各語義軸的有限區間，再用本工具驗證來源與數值界線。

```bash
python -m spectral_public.cli adapter-check examples/p2_requests.json examples/p2_predictions.json
python -m spectral_public.cli evaluate examples/p2_requests.json examples/p2_predictions.json examples/p2_heldout.json
```

測試夾具所有標註與輸出都是**虛構的示範數字**，不是 AI 真實學會語義的實驗證據。評估中的 `point_coverage` 僅表示外部指定的數值標註是否落在預測區間，**不是機率校準**。使用自己的模型前，請閱讀 [`P2_MODEL_ADAPTER.md`](P2_MODEL_ADAPTER.md)，並確保個資、資料授權、標註隔離與保留測試集均符合需求。

原有 `.isl` 語法仍為 `isl 0.1;`，P2 的 v0.2.0 只是增添獨立的交換與評估能力，不代表語法發生不相容變更。


## P3：語義數值檢索與受控輸出

```bash
python -m spectral_public.cli retrieve examples/p3_corpus.json examples/p3_query.json
python -m spectral_public.cli retrieve examples/p3_corpus.json examples/p3_query.json --index lsh
python -m spectral_public.cli retrieval-audit examples/p3_corpus.json examples/p3_query.json
python -m spectral_public.cli controlled-output examples/p3_corpus.json examples/p3_query.json --style evidence
```

P3 仍然只處理已給定的數值區間。LSH 可能遺漏候選，因此必須與完整掃描作實際比較；通過篩選的數值不代表推論為真。輸出的文字是確定性模板，不是 AI 生成內容，也不是原始文件的無損還原。詳細規格見 [`P3_RETRIEVAL_AND_OUTPUT.md`](P3_RETRIEVAL_AND_OUTPUT.md)。

## P4：獨立 JavaScript 版本與一致性測試

不需要安裝 Python 即可單獨運作的 Node.js 解譯器（需要 Node.js 20 以上）：

```bash
node js/cli.mjs run examples/hello.isl
node js/cli.mjs retrieve examples/p3_corpus.json examples/p3_query.json
node js/cli.mjs controlled-output examples/p3_corpus.json examples/p3_query.json evidence
node --test js/tests/p4.test.mjs
```

若要和 Python 參考實作進行相容性比較，才需要兩種語言同時存在：

```bash
python scripts/p4_conformance.py
```

本階段只獨立實作 P1 語言與 P3 精確掃描／受控輸出；不代表外部第三方已驗證，也不代表通用語義理解、模型訓練或 ISQL 內部機制已公開。更多說明見 `docs/P4_INDEPENDENT_CONFORMANCE.md`。

## P5：外部實作相容性測試

P5 的新增重點是讓其他開發者可以從公開規格自行實作，再使用 `scripts/p5_external_gate.py` 進行黑箱測試。驗證器不需要引入 ISL Python 或 Node.js 程式碼來產生預期答案；它使用固定 Golden Files 與自行依規格運算的合成測試。

目前 GitHub CI 執行的是**專案自己維護的兩個版本**，因此只能稱為專案內的跨實作與驗證器測試，不能冒稱已有外部第三方審計。詳細使用與提交方式見 `docs/P5_EXTERNAL_CONFORMANCE_KIT.md`。

這是獨立對外公開版；MIT 授權僅適用於本倉庫內容，不涉及其他未公開研究系統。
