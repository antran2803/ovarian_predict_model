# Implementation Plan - Expert Refactor

## Pham vi Phan 1

Refactor logic dung chung tu `models/tabular_expert.py` vao `models/base_expert.py`, sau do tao ba class mong `TabularExpert`, `UltrasoundExpert` va `MRIExpert`. Phan 1 chi kiem tra pipeline tren mock; chua build dataset that va chua chay Late Fusion.

## Lam gi va loi ich

- `BaseExpert` nhan `feature_list` va `model_type`, giup mot logic duoc dung cho nhieu modality ma khong hardcode ten cot.
- Giữ ba nhanh model hien co: Logistic Regression va Random Forest dung median imputation; LightGBM dung native missing handling va category levels duoc khoa tu fit sang predict.
- Cac class modality chi truyen feature list tu `MODALITY_FEATURES`, de schema la nguon duy nhat ve thu tu va ten feature.
- Bo sung API chung `fit`, `predict_proba`, `predict`, `evaluate` va kiem tra input de cac buoc LOOCV sau nay dung cung mot giao dien.

## Bat cap va rui ro

- Tap mock rat nho, co the co cot toan missing hoac chi co mot lop; day la canh bao pipeline, khong phai bang chung hieu nang.
- Categorical features khac nhau giua modality; mapping phai duoc tao dong theo feature list va khoa category sau fit.
- Input thieu modality khong duoc bi impute roi tao du doan gia; availability se duoc kiem tra o lop model/dataset.
- Mot fold LOOCV co the chi con mot lop; Phan 1 chi xac nhan fit/predict, xu ly fold se duoc chot trong Phan 3.
- LightGBM co the can xu ly truong hop tap fit chi co mot nhan; khong duoc bo qua canh bao.

## Ly do chon tham so

- `model_type` gioi han trong `logistic`, `random_forest`, `lightgbm` de giu tuong thich voi code hien tai.
- `random_state=42` giu ket qua tai lap.
- Logistic Regression giu `max_iter=1000` de tranh khong hoi tu tren feature da scale/imbalance; RF giu 100 cay nhu baseline hien co; LightGBM giu `n_estimators=100`, `min_child_samples=1`, `class_weight="balanced"` theo baseline da chot.
- `SimpleImputer(strategy="median")` chi ap dung cho Logistic/RF nhu quyet dinh hien tai; LightGBM khong impute de giu native NaN.

## Thu tu thuc hien va kiem chung

1. Doc va trich logic hien co cua `TabularExpert`.
2. Tao `BaseExpert`, chuyen logic dung chung, giu API tuong thich toi thieu.
3. Chuyen `TabularExpert` thanh wrapper va tao hai wrapper imaging.
4. Chay smoke test tren mock cho ca ba class va ba model type neu du lieu cho phep.
5. Ghi output that vao `.agents/shared-task.md`, cap nhat CHANGELOG sau khi Phan 1 hoan tat.
6. Dung lai de bao cao; khong sang Phan 2 trong cung mot lan neu chua co xac nhan/review.

## Pham vi Phan 3

Tao `scripts/evaluate_experts_loocv.py` de chay LOOCV doc lap cho Tabular,
Ultrasound va MRI tren dataset that da loc o Phan 2. Moi modality chay ba
`model_type`: `logistic`, `random_forest`, `lightgbm`.

## Lam gi va loi ich

- Moi vong LOOCV chi fit tren phan train cua vong do, sau do du doan dung 1 ca
	test; preprocessing va categorical levels khong duoc hoc truoc ngoai fold.
- Xuat prediction o dang long voi `expert`, `model_type`, `patient_id`, `label`
	va `p_cancer`, de truy vet tung du doan; xuat them metrics theo cap
	expert/model.
- Metrics gom ROC-AUC, sensitivity, specificity, F1, Brier score va TP/FP/TN/FN.
- Output console va metrics CSV phai co canh bao N nho va ghi ro LightGBM dang
	dung them categorical features o Tabular/Ultrasound.

## Bat cap va rui ro

- N moi expert chi 9-11, nen metrics co the thay doi manh theo mot ca va khong
	co y nghia hieu nang lam sang.
- Logistic/RF hien chi dung numeric features, LightGBM dung ca categorical;
	day la so sanh pipeline khong cong bang tuyet doi, khong duoc xep hang model
	theo AUC nhu ket luan thuat toan.
- Neu mot fold chi con mot lop, model phai duoc bo qua co ghi ro thay vi de
	script crash am tham; voi phan bo hien tai du kien train fold van co hai lop.
- Chi dung dataset tu `prepare_real_expert_datasets.py`; khong dung mock hay
	`data/real/*.py` cu, khong dua Case 12 vao bat ky fold nao.

## Cach kiem chung

1. Compile script va chay checksum Ground Truth truoc khi doc dataset.
2. Chay script, xac nhan 90 lan fit/predict (9+11+10 ca x 3 model), khong co
	 Case 12 trong prediction CSV.
3. Kiem tra prediction CSV co 90 dong va metrics CSV co 9 dong; doi chieu
	 phan bo label voi ket qua Phan 2.
4. Chi sau khi cac check tren dat moi cap nhat shared-task va bao cao; khong
	 chay Late Fusion trong task nay.

## Pham vi Late Fusion tiep theo

Late Fusion se nhan output probability tu cac Expert doc lap va tao
`P(cancer)` cuoi cho tung benh nhan. Giai doan nay khong dung lai output cua
chinh benh nhan do de fit model; moi danh gia phai dung cac prediction
out-of-fold trong `results/real_experts_loocv_predictions.csv`.

## Plan de hai agent thong nhat truoc khi code

1. **Nguon probability**: Dung cot `p_cancer` tu LOOCV, join theo
	 `patient_id`; khong dung cac prediction in-sample va khong dua Case 12 vao
	 metric co giam sat.
2. **Model cua moi Expert**: Chua tu y chon theo AUC. De xuat chay truoc
	 toan bo 27 to hop (3 Expert x 3 model_type x 3 chien luoc), hoac neu can
	 mot baseline de doc thi chon Logistic cho ca 3 Expert va ghi ro day la
	 baseline, khong phai model toi uu.
3. **Chien luoc fusion**: Ho tro va so sanh `simple_average` tren probability
	 va voting `AND`, `OR`, `max` tren prediction nhi phan theo paper. Weighted
	 average chi lam khi co quy tac trong validation; khong toi uu trong cung
	 tap LOOCV.
4. **Missing modality**: Chi fuse cac Expert co probability hop le cho ca
	 do, sau do renormalize simple average. Neu khong co Expert nao thi tra
	 `P_fusion=None`, `experts_used=[]`, khong gan 0.5.
5. **Danh gia**: Tinh ROC-AUC, sensitivity, specificity, F1, Brier va
	 TP/FP/TN/FN tren cac ca ma chien luoc co output; ghi ro so ca duoc danh
	 gia moi chien luoc va khong gop nham voi N=12.
6. **Threshold**: 0.5 chi la demo threshold de so sanh pipeline. Khong tu
	 nhan day la threshold lam sang; threshold chinh thuc phai chon tren
	 validation rieng khi co du lieu.

## Rủi ro và điều kiện dừng

- Cac prediction cua ba Expert khong co cung tap patient vi availability
	khac nhau; join sai co the tao ket qua fusion khong dung. Phai in bang
	so ca va danh sach experts_used.
- Neu dung AUC LOOCV de chon model roi dung lai chinh cac prediction do de
	bao cao, se co nguy co model-selection bias. Cac ket qua hien tai chi la
	exploratory.
- Ba modality co cac model feature space khac nhau; LightGBM co them
	categorical features o Tabular/Ultrasound. Can giu canh bao nay trong
	output fusion.
- Nho hon 11 va missing modality lam cac metric fusion dao dong manh. Moi
	output phai ghi disclaimer y khoa va khong duoc dung lam bang chung trien
	khai.

## Kiem chung truoc khi bao cao

- Test `LateFusion` voi 3, 2, 1 va 0 Expert kha dung, bao gom None/NaN,
	xac nhan renormalize va khong tao du doan khi rong.
- Kiem tra du lieu joined khong co Case 12, khong co duplicate
	`(patient_id, expert, model_type)` va so dong khop CSV LOOCV.
- Chay metrics cho tung chien luoc, luu prediction va metrics vao `results/`
	voi ten file ro rang; khong ghi de cac CSV LOOCV goc.
- Chay checksum truoc khi doc Ground Truth; cap nhat `shared-task.md` va
	`AI_CONTINUATION.md` sau khi co bang chung.
