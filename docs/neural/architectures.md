# Нейросетевые архитектуры

## Обзор

Документация описывает нейросетевые архитектуры, используемые в RSecure для анализа угроз, обнаружения аномалий и принятия решений безопасности.

## 🧠 Основные архитектуры

### 1. Сверточные нейронные сети (CNN)

#### 1D CNN для анализа временных последовательностей
```python
import tensorflow as tf
from tensorflow.keras import layers, models

class TemporalCNN:
    def __init__(self, sequence_length=100, feature_dim=64, num_classes=5):
        self.sequence_length = sequence_length
        self.feature_dim = feature_dim
        self.num_classes = num_classes
        self.model = self._build_model()
    
    def _build_model(self):
        """Построение 1D CNN для временных данных"""
        model = models.Sequential([
            # Первый сверточный блок
            layers.Conv1D(64, 3, activation='relu', padding='same', 
                         input_shape=(self.sequence_length, self.feature_dim)),
            layers.BatchNormalization(),
            layers.MaxPooling1D(2),
            layers.Dropout(0.2),
            
            # Второй сверточный блок
            layers.Conv1D(128, 5, activation='relu', padding='same'),
            layers.BatchNormalization(),
            layers.MaxPooling1D(2),
            layers.Dropout(0.3),
            
            # Третий сверточный блок
            layers.Conv1D(256, 7, activation='relu', padding='same'),
            layers.BatchNormalization(),
            layers.GlobalMaxPooling1D(),
            layers.Dropout(0.4),
            
            # Полносвязные слои
            layers.Dense(128, activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.5),
            
            # Выходной слой
            layers.Dense(self.num_classes, activation='softmax')
        ])
        
        return model
    
    def compile_model(self, learning_rate=0.001):
        """Компиляция модели"""
        self.model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate),
            loss='categorical_crossentropy',
            metrics=['accuracy', 'precision', 'recall']
        )
    
    def train(self, X_train, y_train, X_val=None, y_val=None, epochs=100, batch_size=32):
        """Обучение модели"""
        callbacks = [
            tf.keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True),
            tf.keras.callbacks.ReduceLROnPlateau(factor=0.5, patience=5)
        ]
        
        validation_data = (X_val, y_val) if X_val is not None else None
        
        history = self.model.fit(
            X_train, y_train,
            validation_data=validation_data,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=1
        )
        
        return history
```

#### 2D CNN для анализа изображений и спектрограмм
```python
class SpectrogramCNN:
    def __init__(self, input_shape=(128, 128, 1), num_classes=3):
        self.input_shape = input_shape
        self.num_classes = num_classes
        self.model = self._build_model()
    
    def _build_model(self):
        """Построение 2D CNN для спектрограмм"""
        model = models.Sequential([
            # Первый сверточный блок
            layers.Conv2D(32, (3, 3), activation='relu', padding='same',
                         input_shape=self.input_shape),
            layers.BatchNormalization(),
            layers.Conv2D(32, (3, 3), activation='relu', padding='same'),
            layers.BatchNormalization(),
            layers.MaxPooling2D((2, 2)),
            layers.Dropout(0.25),
            
            # Второй сверточный блок
            layers.Conv2D(64, (3, 3), activation='relu', padding='same'),
            layers.BatchNormalization(),
            layers.Conv2D(64, (3, 3), activation='relu', padding='same'),
            layers.BatchNormalization(),
            layers.MaxPooling2D((2, 2)),
            layers.Dropout(0.35),
            
            # Третий сверточный блок
            layers.Conv2D(128, (3, 3), activation='relu', padding='same'),
            layers.BatchNormalization(),
            layers.GlobalMaxPooling2D(),
            layers.Dropout(0.4),
            
            # Полносвязные слои
            layers.Dense(256, activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.5),
            
            # Выходной слой
            layers.Dense(self.num_classes, activation='softmax')
        ])
        
        return model
```

### 2. Рекуррентные нейронные сети (RNN)

#### LSTM для анализа последовательностей
```python
class LSTMSecurityAnalyzer:
    def __init__(self, sequence_length=50, feature_dim=64, num_classes=5):
        self.sequence_length = sequence_length
        self.feature_dim = feature_dim
        self.num_classes = num_classes
        self.model = self._build_model()
    
    def _build_model(self):
        """Построение LSTM модели"""
        model = models.Sequential([
            # Первый LSTM слой
            layers.LSTM(128, return_sequences=True, 
                       input_shape=(self.sequence_length, self.feature_dim)),
            layers.BatchNormalization(),
            layers.Dropout(0.2),
            
            # Второй LSTM слой
            layers.LSTM(128, return_sequences=True),
            layers.BatchNormalization(),
            layers.Dropout(0.3),
            
            # Третий LSTM слой
            layers.LSTM(64, return_sequences=False),
            layers.BatchNormalization(),
            layers.Dropout(0.4),
            
            # Полносвязные слои
            layers.Dense(64, activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.5),
            
            # Выходной слой
            layers.Dense(self.num_classes, activation='softmax')
        ])
        
        return model
```

#### BiLSTM с механизмом внимания
```python
class BiLSTMWithAttention:
    def __init__(self, sequence_length=50, feature_dim=64, num_classes=5):
        self.sequence_length = sequence_length
        self.feature_dim = feature_dim
        self.num_classes = num_classes
        self.model = self._build_model()
    
    def _build_model(self):
        """Построение双向LSTM с механизмом внимания"""
        inputs = layers.Input(shape=(self.sequence_length, self.feature_dim))
        
        # BiLSTM слои
        lstm_out = layers.Bidirectional(
            layers.LSTM(128, return_sequences=True)
        )(inputs)
        lstm_out = layers.BatchNormalization()(lstm_out)
        lstm_out = layers.Dropout(0.2)(lstm_out)
        
        # Механизм внимания
        attention = layers.MultiHeadAttention(
            num_heads=8, key_dim=16
        )(lstm_out, lstm_out)
        
        # Остаточное соединение
        x = layers.Add()([lstm_out, attention])
        x = layers.LayerNormalization()(x)
        
        # Глобальный пулинг
        x = layers.GlobalAveragePooling1D()(x)
        x = layers.Dropout(0.4)(x)
        
        # Полносвязные слои
        x = layers.Dense(128, activation='relu')(x)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.5)(x)
        
        # Выходной слой
        outputs = layers.Dense(self.num_classes, activation='softmax')(x)
        
        model = tf.keras.Model(inputs=inputs, outputs=outputs)
        return model
```

### 3. Трансформер архитектуры

#### Трансформер для анализа временных рядов
```python
class TransformerSecurityAnalyzer:
    def __init__(self, sequence_length=100, feature_dim=64, num_classes=5, d_model=128):
        self.sequence_length = sequence_length
        self.feature_dim = feature_dim
        self.num_classes = num_classes
        self.d_model = d_model
        self.model = self._build_model()
    
    def _build_model(self):
        """Построение Трансформер модели"""
        # Входной слой
        inputs = layers.Input(shape=(self.sequence_length, self.feature_dim))
        
        # Проекция входных данных
        x = layers.Dense(self.d_model)(inputs)
        
        # Позиционное кодирование
        x = self._add_positional_encoding(x)
        
        # Трансформер блоки
        for _ in range(4):  # 4 трансформер блока
            x = self._transformer_block(x, num_heads=8, dff=512)
        
        # Глобальный пулинг
        x = layers.GlobalAveragePooling1D()(x)
        x = layers.Dropout(0.4)(x)
        
        # Полносвязные слои
        x = layers.Dense(128, activation='relu')(x)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.5)(x)
        
        # Выходной слой
        outputs = layers.Dense(self.num_classes, activation='softmax')(x)
        
        model = tf.keras.Model(inputs=inputs, outputs=outputs)
        return model
    
    def _add_positional_encoding(self, inputs):
        """Добавление позиционного кодирования"""
        seq_len = tf.shape(inputs)[1]
        
        # Создание позиционных кодировок
        positions = tf.range(seq_len, dtype=tf.float32)[:, tf.newaxis]
        depths = tf.range(self.d_model, dtype=tf.float32)[tf.newaxis, :] / self.d_model
        
        angle_rates = 1 / (10000 ** depths)
        angle_rads = positions * angle_rates
        
        # Синус и косинус для четных и нечетных позиций
        sines = tf.math.sin(angle_rads[:, 0::2])
        cosines = tf.math.cos(angle_rads[:, 1::2])
        
        pos_encoding = tf.concat([sines, cosines], axis=-1)
        pos_encoding = pos_encoding[tf.newaxis, ...]
        
        return inputs + pos_encoding
    
    def _transformer_block(self, x, num_heads, dff, dropout_rate=0.1):
        """Трансформер блок"""
        # Многоголовое внимание
        attn_output = layers.MultiHeadAttention(
            num_heads=num_heads, key_dim=x.shape[-1] // num_heads
        )(x, x)
        attn_output = layers.Dropout(dropout_rate)(attn_output)
        out1 = layers.LayerNormalization()(x + attn_output)
        
        # Полносвязная сеть
        ffn_output = layers.Dense(dff, activation='relu')(out1)
        ffn_output = layers.Dense(x.shape[-1])(ffn_output)
        ffn_output = layers.Dropout(dropout_rate)(ffn_output)
        out2 = layers.LayerNormalization()(out1 + ffn_output)
        
        return out2
```

## 🎯 Специализированные архитектуры

### 1. Автоэнкодеры для обнаружения аномалий

#### Вариационный автоэнкодер (VAE)
```python
class VAEAnomalyDetector:
    def __init__(self, input_dim=64, latent_dim=16):
        self.input_dim = input_dim
        self.latent_dim = latent_dim
        self.encoder = self._build_encoder()
        self.decoder = self._build_decoder()
        self.vae = self._build_vae()
    
    def _build_encoder(self):
        """Построение энкодера"""
        inputs = layers.Input(shape=(self.input_dim,))
        
        x = layers.Dense(128, activation='relu')(inputs)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.2)(x)
        
        x = layers.Dense(64, activation='relu')(x)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.2)(x)
        
        # Параметры распределения
        z_mean = layers.Dense(self.latent_dim)(x)
        z_log_var = layers.Dense(self.latent_dim)(x)
        
        return tf.keras.Model(inputs, [z_mean, z_log_var])
    
    def _build_decoder(self):
        """Построение декодера"""
        inputs = layers.Input(shape=(self.latent_dim,))
        
        x = layers.Dense(64, activation='relu')(inputs)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.2)(x)
        
        x = layers.Dense(128, activation='relu')(x)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.2)(x)
        
        outputs = layers.Dense(self.input_dim, activation='sigmoid')(x)
        
        return tf.keras.Model(inputs, outputs)
    
    def _build_vae(self):
        """Построение VAE"""
        inputs = layers.Input(shape=(self.input_dim,))
        z_mean, z_log_var = self.encoder(inputs)
        
        # Сэмплирование с использованием трюка репараметризации
        z = self._sampling([z_mean, z_log_var])
        reconstructed = self.decoder(z)
        
        # Модель VAE
        vae = tf.keras.Model(inputs, reconstructed)
        
        # Добавление потерь
        reconstruction_loss = tf.keras.losses.mse(inputs, reconstructed)
        reconstruction_loss *= self.input_dim
        kl_loss = 1 + z_log_var - tf.square(z_mean) - tf.exp(z_log_var)
        kl_loss = tf.reduce_mean(kl_loss)
        kl_loss *= -0.5
        
        vae_loss = tf.reduce_mean(reconstruction_loss + kl_loss)
        vae.add_loss(vae_loss)
        
        return vae
    
    def _sampling(self, args):
        """Сэмплирование из латентного распределения"""
        z_mean, z_log_var = args
        batch = tf.shape(z_mean)[0]
        dim = tf.shape(z_mean)[1]
        epsilon = tf.keras.backend.random_normal(shape=(batch, dim))
        return z_mean + tf.exp(0.5 * z_log_var) * epsilon
    
    def detect_anomalies(self, data, threshold=2.0):
        """Обнаружение аномалий на основе реконструкции"""
        reconstructed = self.vae.predict(data)
        
        # Расчет ошибки реконструкции
        reconstruction_error = np.mean(np.square(data - reconstructed), axis=1)
        
        # Пороговое обнаружение
        mean_error = np.mean(reconstruction_error)
        std_error = np.std(reconstruction_error)
        threshold_value = mean_error + threshold * std_error
        
        anomalies = reconstruction_error > threshold_value
        
        return {
            'reconstruction_error': reconstruction_error,
            'threshold': threshold_value,
            'anomalies': anomalies,
            'anomaly_indices': np.where(anomalies)[0]
        }
```

### 2. Генеративные состязательные сети (GAN)

#### GAN для генерации нормальных паттернов
```python
class SecurityGAN:
    def __init__(self, input_dim=64, latent_dim=32):
        self.input_dim = input_dim
        self.latent_dim = latent_dim
        self.generator = self._build_generator()
        self.discriminator = self._build_discriminator()
        self.gan = self._build_gan()
    
    def _build_generator(self):
        """Построение генератора"""
        model = tf.keras.Sequential([
            layers.Dense(128, activation='relu', input_dim=self.latent_dim),
            layers.BatchNormalization(),
            layers.Dropout(0.2),
            
            layers.Dense(256, activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.2),
            
            layers.Dense(512, activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.2),
            
            layers.Dense(self.input_dim, activation='tanh')
        ])
        
        return model
    
    def _build_discriminator(self):
        """Построение дискриминатора"""
        model = tf.keras.Sequential([
            layers.Dense(512, activation='relu', input_dim=self.input_dim),
            layers.Dropout(0.3),
            
            layers.Dense(256, activation='relu'),
            layers.Dropout(0.3),
            
            layers.Dense(128, activation='relu'),
            layers.Dropout(0.3),
            
            layers.Dense(1, activation='sigmoid')
        ])
        
        return model
    
    def _build_gan(self):
        """Построение GAN"""
        self.discriminator.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.0002),
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        self.discriminator.trainable = False
        
        gan_input = layers.Input(shape=(self.latent_dim,))
        generated_data = self.generator(gan_input)
        gan_output = self.discriminator(generated_data)
        
        gan = tf.keras.Model(gan_input, gan_output)
        gan.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.0002),
            loss='binary_crossentropy'
        )
        
        return gan
    
    def train(self, real_data, epochs=1000, batch_size=32):
        """Обучение GAN"""
        for epoch in range(epochs):
            # Обучение дискриминатора
            idx = np.random.randint(0, real_data.shape[0], batch_size // 2)
            real_samples = real_data[idx]
            
            noise = np.random.normal(0, 1, (batch_size // 2, self.latent_dim))
            fake_samples = self.generator.predict(noise)
            
            # Комбинирование реальных и сгенерированных данных
            combined_samples = np.vstack([real_samples, fake_samples])
            labels = np.vstack([np.ones((batch_size // 2, 1)), np.zeros((batch_size // 2, 1))])
            
            d_loss = self.discriminator.train_on_batch(combined_samples, labels)
            
            # Обучение генератора
            noise = np.random.normal(0, 1, (batch_size, self.latent_dim))
            labels_gan = np.ones((batch_size, 1))
            
            g_loss = self.gan.train_on_batch(noise, labels_gan)
            
            if epoch % 100 == 0:
                print(f"Epoch {epoch}: D_loss={d_loss[0]}, G_loss={g_loss}")
```

### 3. Графовые нейронные сети (GNN)

#### GNN для анализа сетевых связей
```python
import tensorflow as tf
from tensorflow.keras import layers

class GraphSecurityAnalyzer:
    def __init__(self, node_features=64, edge_features=8, num_classes=3):
        self.node_features = node_features
        self.edge_features = edge_features
        self.num_classes = num_classes
        self.model = self._build_model()
    
    def _build_model(self):
        """Построение GNN модели"""
        # Входные слои
        nodes_input = layers.Input(shape=(None, self.node_features))
        edges_input = layers.Input(shape=(None, None, self.edge_features))
        adjacency_input = layers.Input(shape=(None, None))
        
        # Сверточные слои на графах
        x = self._graph_conv_layer(nodes_input, adjacency_input, 128)
        x = layers.BatchNormalization()(x)
        x = layers.ReLU()(x)
        x = layers.Dropout(0.2)(x)
        
        x = self._graph_conv_layer(x, adjacency_input, 64)
        x = layers.BatchNormalization()(x)
        x = layers.ReLU()(x)
        x = layers.Dropout(0.3)(x)
        
        # Глобальный пулинг
        x = layers.GlobalAveragePooling1D()(x)
        x = layers.Dropout(0.4)(x)
        
        # Полносвязные слои
        x = layers.Dense(32, activation='relu')(x)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.5)(x)
        
        # Выходной слой
        outputs = layers.Dense(self.num_classes, activation='softmax')(x)
        
        model = tf.keras.Model(
            inputs=[nodes_input, edges_input, adjacency_input],
            outputs=outputs
        )
        
        return model
    
    def _graph_conv_layer(self, node_features, adjacency, output_dim):
        """Сверточный слой на графе"""
        # Преобразование размерности
        node_dim = tf.shape(node_features)[-1]
        
        # Линейное преобразование
        weights = tf.keras.layers.Dense(output_dim)(node_features)
        
        # Свертка на графе
        convolved = tf.linalg.matmul(adjacency, weights)
        
        return convolved
```

## 🔧 Ансамблевые архитектуры

### 1. Голосование моделей
```python
class EnsembleSecurityModel:
    def __init__(self, models):
        self.models = models
        self.weights = None
    
    def predict(self, data):
        """Ансамблевое предсказание"""
        predictions = []
        
        for model in self.models:
            pred = model.predict(data)
            predictions.append(pred)
        
        # Взвешенное голосование
        if self.weights is not None:
            weighted_preds = np.average(predictions, axis=0, weights=self.weights)
        else:
            weighted_preds = np.mean(predictions, axis=0)
        
        return weighted_preds
    
    def set_weights(self, weights):
        """Установка весов моделей"""
        if len(weights) == len(self.models):
            self.weights = np.array(weights) / np.sum(weights)
        else:
            raise ValueError("Number of weights must match number of models")
```

### 2. Стекинг
```python
class StackingEnsemble:
    def __init__(self, base_models, meta_model):
        self.base_models = base_models
        self.meta_model = meta_model
        self.fitted = False
    
    def fit(self, X, y, cv=5):
        """Обучение ансамбля"""
        from sklearn.model_selection import KFold
        
        # Обучение базовых моделей
        base_predictions = np.zeros((X.shape[0], len(self.base_models)))
        
        kf = KFold(n_splits=cv)
        for train_idx, val_idx in kf.split(X):
            X_train, X_val = X[train_idx], X[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]
            
            for i, model in enumerate(self.base_models):
                model.fit(X_train, y_train)
                pred = model.predict(X_val)
                base_predictions[val_idx, i] = pred
        
        # Обучение мета-модели
        self.meta_model.fit(base_predictions, y)
        
        # Обучение базовых моделей на всех данных
        for model in self.base_models:
            model.fit(X, y)
        
        self.fitted = True
    
    def predict(self, X):
        """Предсказание ансамбля"""
        if not self.fitted:
            raise ValueError("Model not fitted")
        
        # Предсказания базовых моделей
        base_predictions = np.zeros((X.shape[0], len(self.base_models)))
        
        for i, model in enumerate(self.base_models):
            pred = model.predict(X)
            base_predictions[:, i] = pred
        
        # Предсказание мета-модели
        return self.meta_model.predict(base_predictions)
```

## 📊 Оптимизация и производительность

### 1. Квантование моделей
```python
def quantize_model(model, X_sample):
    """Квантование модели для оптимизации"""
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    
    # Оптимизация
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    
    # Представительный набор данных для квантования
    def representative_dataset():
        for _ in range(100):
            yield [X_sample[np.random.randint(0, len(X_sample))].astype(np.float32)]
    
    converter.representative_dataset = representative_dataset
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    converter.inference_input_type = tf.int8
    converter.inference_output_type = tf.int8
    
    quantized_model = converter.convert()
    
    return quantized_model
```

### 2. Прагматическая оптимизация
```python
def optimize_model_for_inference(model):
    """Оптимизация модели для инференса"""
    # Замена BatchNormalization на предвычисленные значения
    for layer in model.layers:
        if isinstance(layer, layers.BatchNormalization):
            # Интеграция в предыдущий слой
            if hasattr(layer, 'gamma'):
                # Вычисление скейлинга и сдвига
                scale = layer.gamma / np.sqrt(layer.epsilon + layer.moving_variance)
                shift = layer.beta - scale * layer.moving_mean
                
                # Применение к предыдущему слою
                if hasattr(model.layers[model.layers.index(layer) - 1], 'kernel'):
                    prev_layer = model.layers[model.layers.index(layer) - 1]
                    prev_layer.kernel.assign(prev_layer.kernel * scale)
                    if hasattr(prev_layer, 'bias'):
                        prev_layer.bias.assign(prev_layer.bias * scale + shift)
    
    return model
```

## 🚀 Практическое применение

### Интеграция с RSecure
```python
class RSecureNeuralCore:
    def __init__(self):
        # Инициализация специализированных моделей
        self.network_analyzer = TemporalCNN(
            sequence_length=100, feature_dim=64, num_classes=5
        )
        self.behavior_analyzer = BiLSTMWithAttention(
            sequence_length=50, feature_dim=32, num_classes=3
        )
        self.spectral_analyzer = SpectrogramCNN(
            input_shape=(128, 128, 1), num_classes=4
        )
        
        # Ансамблевая модель
        self.ensemble = EnsembleSecurityModel([
            self.network_analyzer.model,
            self.behavior_analyzer.model,
            self.spectral_analyzer.model
        ])
        
        # Обучение моделей
        self._train_models()
    
    def analyze_threats(self, data):
        """Комплексный анализ угроз"""
        results = {}
        
        # Анализ сетевых данных
        if 'network' in data:
            results['network'] = self.network_analyzer.model.predict(data['network'])
        
        # Анализ поведенческих данных
        if 'behavior' in data:
            results['behavior'] = self.behavior_analyzer.model.predict(data['behavior'])
        
        # Анализ спектральных данных
        if 'spectral' in data:
            results['spectral'] = self.spectral_analyzer.model.predict(data['spectral'])
        
        # Ансамблевое предсказание
        if len(results) > 1:
            combined_data = np.concatenate(list(results.values()), axis=1)
            ensemble_prediction = self.ensemble.predict(combined_data)
            results['ensemble'] = ensemble_prediction
        
        return results
    
    def _train_models(self):
        """Обучение моделей на исторических данных"""
        # Загрузка данных
        training_data = self._load_training_data()
        
        # Обучение каждой модели
        for data_type, (X, y) in training_data.items():
            if data_type == 'network':
                self.network_analyzer.train(X, y)
            elif data_type == 'behavior':
                self.behavior_analyzer.train(X, y)
            elif data_type == 'spectral':
                self.spectral_analyzer.train(X, y)
```

---

*Документация актуальна для версии RSecure 1.0+*
