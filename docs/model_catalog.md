# Model catalog

Full Nixtla model directory tracked by `tsforecasting`, with source URL and validation status. Independent of the build-time `REGISTRY` presets — `cataloged` models are listed but not verified runnable.

**Status counts**: cataloged=67, mvp_smoke=11, validated=0, blocked=0, deprecated=0  (total = 78)

## statsforecast (35)

| name | class_path | model_type | status | source |
| --- | --- | --- | --- | --- |
| adida | `statsforecast.models.ADIDA` | croston | cataloged | [doc](https://nixtlaverse.nixtla.io/statsforecast/docs/models.html) |
| arch | `statsforecast.models.ARCH` | garch | cataloged | [doc](https://nixtlaverse.nixtla.io/statsforecast/docs/models.html) |
| arima | `statsforecast.models.ARIMA` | arima | cataloged | [doc](https://nixtlaverse.nixtla.io/statsforecast/docs/models.html) |
| auto_arima | `statsforecast.models.AutoARIMA` | arima | cataloged | [doc](https://nixtlaverse.nixtla.io/statsforecast/docs/models.html) |
| auto_ces | `statsforecast.models.AutoCES` | ces | cataloged | [doc](https://nixtlaverse.nixtla.io/statsforecast/docs/models.html) |
| auto_ets | `statsforecast.models.AutoETS` | ets | mvp_smoke | [doc](https://nixtlaverse.nixtla.io/statsforecast/docs/models.html) |
| auto_mfles | `statsforecast.models.AutoMFLES` | mfles | cataloged | [doc](https://nixtlaverse.nixtla.io/statsforecast/docs/models.html) |
| auto_regressive | `statsforecast.models.AutoRegressive` | arima | cataloged | [doc](https://nixtlaverse.nixtla.io/statsforecast/docs/models.html) |
| auto_tbats | `statsforecast.models.AutoTBATS` | tbats | cataloged | [doc](https://nixtlaverse.nixtla.io/statsforecast/docs/models.html) |
| auto_theta | `statsforecast.models.AutoTheta` | theta | cataloged | [doc](https://nixtlaverse.nixtla.io/statsforecast/docs/models.html) |
| croston_classic | `statsforecast.models.CrostonClassic` | croston | cataloged | [doc](https://nixtlaverse.nixtla.io/statsforecast/docs/models.html) |
| croston_optimized | `statsforecast.models.CrostonOptimized` | croston | cataloged | [doc](https://nixtlaverse.nixtla.io/statsforecast/docs/models.html) |
| croston_sba | `statsforecast.models.CrostonSBA` | croston | cataloged | [doc](https://nixtlaverse.nixtla.io/statsforecast/docs/models.html) |
| dynamic_optimized_theta | `statsforecast.models.DynamicOptimizedTheta` | theta | cataloged | [doc](https://nixtlaverse.nixtla.io/statsforecast/docs/models.html) |
| dynamic_theta | `statsforecast.models.DynamicTheta` | theta | cataloged | [doc](https://nixtlaverse.nixtla.io/statsforecast/docs/models.html) |
| garch | `statsforecast.models.GARCH` | garch | cataloged | [doc](https://nixtlaverse.nixtla.io/statsforecast/docs/models.html) |
| historic_average | `statsforecast.models.HistoricAverage` | naive | cataloged | [doc](https://nixtlaverse.nixtla.io/statsforecast/docs/models.html) |
| holt | `statsforecast.models.Holt` | exponential | cataloged | [doc](https://nixtlaverse.nixtla.io/statsforecast/docs/models.html) |
| holt_winters | `statsforecast.models.HoltWinters` | exponential | cataloged | [doc](https://nixtlaverse.nixtla.io/statsforecast/docs/models.html) |
| imapa | `statsforecast.models.IMAPA` | croston | cataloged | [doc](https://nixtlaverse.nixtla.io/statsforecast/docs/models.html) |
| mfles | `statsforecast.models.MFLES` | mfles | cataloged | [doc](https://nixtlaverse.nixtla.io/statsforecast/docs/models.html) |
| mstl | `statsforecast.models.MSTL` | decomposition | cataloged | [doc](https://nixtlaverse.nixtla.io/statsforecast/docs/models.html) |
| naive | `statsforecast.models.Naive` | naive | cataloged | [doc](https://nixtlaverse.nixtla.io/statsforecast/docs/models.html) |
| optimized_theta | `statsforecast.models.OptimizedTheta` | theta | cataloged | [doc](https://nixtlaverse.nixtla.io/statsforecast/docs/models.html) |
| random_walk_with_drift | `statsforecast.models.RandomWalkWithDrift` | naive | cataloged | [doc](https://nixtlaverse.nixtla.io/statsforecast/docs/models.html) |
| seasonal_exp_smoothing | `statsforecast.models.SeasonalExponentialSmoothing` | exponential | cataloged | [doc](https://nixtlaverse.nixtla.io/statsforecast/docs/models.html) |
| seasonal_exp_smoothing_optimized | `statsforecast.models.SeasonalExponentialSmoothingOptimized` | exponential | cataloged | [doc](https://nixtlaverse.nixtla.io/statsforecast/docs/models.html) |
| seasonal_naive | `statsforecast.models.SeasonalNaive` | naive | mvp_smoke | [doc](https://nixtlaverse.nixtla.io/statsforecast/docs/models.html) |
| seasonal_window_average | `statsforecast.models.SeasonalWindowAverage` | naive | cataloged | [doc](https://nixtlaverse.nixtla.io/statsforecast/docs/models.html) |
| simple_exp_smoothing | `statsforecast.models.SimpleExponentialSmoothing` | exponential | cataloged | [doc](https://nixtlaverse.nixtla.io/statsforecast/docs/models.html) |
| simple_exp_smoothing_optimized | `statsforecast.models.SimpleExponentialSmoothingOptimized` | exponential | cataloged | [doc](https://nixtlaverse.nixtla.io/statsforecast/docs/models.html) |
| tbats | `statsforecast.models.TBATS` | tbats | cataloged | [doc](https://nixtlaverse.nixtla.io/statsforecast/docs/models.html) |
| theta | `statsforecast.models.Theta` | theta | cataloged | [doc](https://nixtlaverse.nixtla.io/statsforecast/docs/models.html) |
| tsb | `statsforecast.models.TSB` | croston | cataloged | [doc](https://nixtlaverse.nixtla.io/statsforecast/docs/models.html) |
| window_average | `statsforecast.models.WindowAverage` | naive | cataloged | [doc](https://nixtlaverse.nixtla.io/statsforecast/docs/models.html) |

## mlforecast (8)

| name | class_path | model_type | status | source |
| --- | --- | --- | --- | --- |
| elastic_net | `sklearn.linear_model.ElasticNet` | linear | mvp_smoke | [doc](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.ElasticNet.html) |
| hist_gradient_boosting | `sklearn.ensemble.HistGradientBoostingRegressor` | tree | mvp_smoke | [doc](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.HistGradientBoostingRegressor.html) |
| kneighbors | `sklearn.neighbors.KNeighborsRegressor` | neighbors | cataloged | [doc](https://scikit-learn.org/stable/modules/generated/sklearn.neighbors.KNeighborsRegressor.html) |
| lasso | `sklearn.linear_model.Lasso` | linear | mvp_smoke | [doc](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.Lasso.html) |
| linear_regression | `sklearn.linear_model.LinearRegression` | linear | mvp_smoke | [doc](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LinearRegression.html) |
| random_forest | `sklearn.ensemble.RandomForestRegressor` | tree | mvp_smoke | [doc](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestRegressor.html) |
| ridge | `sklearn.linear_model.Ridge` | linear | mvp_smoke | [doc](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.Ridge.html) |
| svr | `sklearn.svm.SVR` | svm | cataloged | [doc](https://scikit-learn.org/stable/modules/generated/sklearn.svm.SVR.html) |

## neuralforecast (35)

| name | class_path | model_type | status | source |
| --- | --- | --- | --- | --- |
| autoformer | `neuralforecast.models.Autoformer` | neural | cataloged | [doc](https://nixtlaverse.nixtla.io/neuralforecast/docs/models.html) |
| bitcn | `neuralforecast.models.BiTCN` | neural | cataloged | [doc](https://nixtlaverse.nixtla.io/neuralforecast/docs/models.html) |
| deepar | `neuralforecast.models.DeepAR` | neural | cataloged | [doc](https://nixtlaverse.nixtla.io/neuralforecast/docs/models.html) |
| deepnpts | `neuralforecast.models.DeepNPTS` | neural | cataloged | [doc](https://nixtlaverse.nixtla.io/neuralforecast/docs/models.html) |
| dilated_rnn | `neuralforecast.models.DilatedRNN` | neural | cataloged | [doc](https://nixtlaverse.nixtla.io/neuralforecast/docs/models.html) |
| dlinear | `neuralforecast.models.DLinear` | neural | cataloged | [doc](https://nixtlaverse.nixtla.io/neuralforecast/docs/models.html) |
| fedformer | `neuralforecast.models.FEDformer` | neural | cataloged | [doc](https://nixtlaverse.nixtla.io/neuralforecast/docs/models.html) |
| gru | `neuralforecast.models.GRU` | neural | cataloged | [doc](https://nixtlaverse.nixtla.io/neuralforecast/docs/models.html) |
| informer | `neuralforecast.models.Informer` | neural | cataloged | [doc](https://nixtlaverse.nixtla.io/neuralforecast/docs/models.html) |
| itransformer | `neuralforecast.models.iTransformer` | neural | cataloged | [doc](https://nixtlaverse.nixtla.io/neuralforecast/docs/models.html) |
| kan | `neuralforecast.models.KAN` | neural | cataloged | [doc](https://nixtlaverse.nixtla.io/neuralforecast/docs/models.html) |
| lstm | `neuralforecast.models.LSTM` | neural | cataloged | [doc](https://nixtlaverse.nixtla.io/neuralforecast/docs/models.html) |
| mlp | `neuralforecast.models.MLP` | neural | cataloged | [doc](https://nixtlaverse.nixtla.io/neuralforecast/docs/models.html) |
| mlp_multivariate | `neuralforecast.models.MLPMultivariate` | neural | cataloged | [doc](https://nixtlaverse.nixtla.io/neuralforecast/docs/models.html) |
| nbeats | `neuralforecast.models.NBEATS` | neural | mvp_smoke | [doc](https://nixtlaverse.nixtla.io/neuralforecast/docs/models.html) |
| nbeatsx | `neuralforecast.models.NBEATSx` | neural | cataloged | [doc](https://nixtlaverse.nixtla.io/neuralforecast/docs/models.html) |
| nhits | `neuralforecast.models.NHITS` | neural | mvp_smoke | [doc](https://nixtlaverse.nixtla.io/neuralforecast/docs/models.html) |
| nhits_quantile | `neuralforecast.models.NHITS` | neural_quantile | mvp_smoke | [doc](https://nixtlaverse.nixtla.io/neuralforecast/docs/models.html) |
| nlinear | `neuralforecast.models.NLinear` | neural | cataloged | [doc](https://nixtlaverse.nixtla.io/neuralforecast/docs/models.html) |
| patchtst | `neuralforecast.models.PatchTST` | neural | cataloged | [doc](https://nixtlaverse.nixtla.io/neuralforecast/docs/models.html) |
| rmok | `neuralforecast.models.RMoK` | neural | cataloged | [doc](https://nixtlaverse.nixtla.io/neuralforecast/docs/models.html) |
| rnn | `neuralforecast.models.RNN` | neural | cataloged | [doc](https://nixtlaverse.nixtla.io/neuralforecast/docs/models.html) |
| softs | `neuralforecast.models.SOFTS` | neural | cataloged | [doc](https://nixtlaverse.nixtla.io/neuralforecast/docs/models.html) |
| stemgnn | `neuralforecast.models.StemGNN` | neural | cataloged | [doc](https://nixtlaverse.nixtla.io/neuralforecast/docs/models.html) |
| tcn | `neuralforecast.models.TCN` | neural | cataloged | [doc](https://nixtlaverse.nixtla.io/neuralforecast/docs/models.html) |
| tft | `neuralforecast.models.TFT` | neural | cataloged | [doc](https://nixtlaverse.nixtla.io/neuralforecast/docs/models.html) |
| tide | `neuralforecast.models.TiDE` | neural | cataloged | [doc](https://nixtlaverse.nixtla.io/neuralforecast/docs/models.html) |
| timellm | `neuralforecast.models.TimeLLM` | neural | cataloged | [doc](https://nixtlaverse.nixtla.io/neuralforecast/docs/models.html) |
| timemixer | `neuralforecast.models.TimeMixer` | neural | cataloged | [doc](https://nixtlaverse.nixtla.io/neuralforecast/docs/models.html) |
| timesnet | `neuralforecast.models.TimesNet` | neural | cataloged | [doc](https://nixtlaverse.nixtla.io/neuralforecast/docs/models.html) |
| timexer | `neuralforecast.models.TimeXer` | neural | cataloged | [doc](https://nixtlaverse.nixtla.io/neuralforecast/docs/models.html) |
| tsmixer | `neuralforecast.models.TSMixer` | neural | cataloged | [doc](https://nixtlaverse.nixtla.io/neuralforecast/docs/models.html) |
| tsmixerx | `neuralforecast.models.TSMixerx` | neural | cataloged | [doc](https://nixtlaverse.nixtla.io/neuralforecast/docs/models.html) |
| vanilla_transformer | `neuralforecast.models.VanillaTransformer` | neural | cataloged | [doc](https://nixtlaverse.nixtla.io/neuralforecast/docs/models.html) |
| xlstm | `neuralforecast.models.xLSTM` | neural | cataloged | [doc](https://nixtlaverse.nixtla.io/neuralforecast/docs/models.html) |
