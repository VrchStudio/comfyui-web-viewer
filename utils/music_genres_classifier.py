import traceback
import os
import time
import argparse
import json
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import torchaudio
from sklearn.model_selection import train_test_split
from torch.utils.data import Dataset, DataLoader
from pydub import AudioSegment


class MusicGenreDataset(Dataset):
    def __init__(self, X, y):
        self.X = torch.FloatTensor(X)
        self.y = torch.LongTensor(y)

    def __len__(self):
        return len(self.y)

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]


class MusicGenreCNN(nn.Module):
    def __init__(self, num_genres, input_length=1291, n_mfcc=13):
        super(MusicGenreCNN, self).__init__()
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, stride=1, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1)
        self.pool = nn.MaxPool2d(2, 2)

        example_input = torch.zeros(1, 1, input_length, n_mfcc)
        conv_output = self._forward_conv(example_input)
        conv_output_size = conv_output.view(1, -1).size(1)

        self.fc1 = nn.Linear(conv_output_size, 128)
        self.fc2 = nn.Linear(128, num_genres)
        self.dropout = nn.Dropout(0.5)

    def _forward_conv(self, x):
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        return x

    def forward(self, x):
        x = x.unsqueeze(1)
        x = self._forward_conv(x)
        x = x.view(x.size(0), -1)
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)
        return x


class MusicGenresClassifier:
    def __init__(self):
        self.genres = []

    def save_genres(self, file_path):
        with open(file_path, 'w') as f:
            json.dump(self.genres, f)

    def load_genres(self, file_path):
        with open(file_path, 'r') as f:
            self.genres = json.load(f)

    def convert_to_wav(self, audio_file):
        temp_dir = os.path.join(os.getcwd(), "temp")
        os.makedirs(temp_dir, exist_ok=True)

        audio = AudioSegment.from_file(audio_file)
        audio = audio.set_frame_rate(44100).set_channels(1).set_sample_width(2)

        wav_file_path = os.path.join(temp_dir, os.path.basename(audio_file).replace(os.path.splitext(audio_file)[-1], '.wav'))
        audio.export(wav_file_path, format="wav")

        return wav_file_path

    def inspect_audio(self, file_path):
        info = torchaudio.info(file_path)
        print(info)

    def extract_features(self, file_path, duration=None, target_length=1291, n_mfcc=13):
        try:
            waveform, sr = torchaudio.load(file_path)

            if duration is not None:
                max_samples = int(sr * duration)
                waveform = waveform[:, :max_samples]

            mfcc = torchaudio.transforms.MFCC(
                sample_rate=sr,
                n_mfcc=n_mfcc,
                melkwargs={'n_mels': 64, 'n_fft': 2048}
            )(waveform)

            mfcc = mfcc.squeeze(0).transpose(0, 1)

            if target_length is not None:
                if mfcc.shape[0] < target_length:
                    mfcc = F.pad(mfcc, (0, 0, 0, target_length - mfcc.shape[0]))
                else:
                    mfcc = mfcc[:target_length, :]

            return mfcc
        except Exception as e:
            print(f"Error processing file {file_path}: {str(e)}")
            traceback.print_exc()
            return None

    def load_dataset(self, dataset_path, enable_debug=False):
        self.genres = ['blues', 'classical', 'country', 'disco', 'hiphop', 'jazz', 'metal', 'pop', 'reggae', 'rock']
        features = []
        labels = []

        if enable_debug:
            print("Starting to load dataset...")

        target_length = 1291

        for genre in self.genres:
            genre_path = os.path.join(dataset_path, genre)
            for file in os.listdir(genre_path):
                if file.endswith('.wav'):
                    file_path = os.path.join(genre_path, file)
                    mfcc_features = self.extract_features(file_path, target_length=target_length)
                    if mfcc_features is not None:
                        features.append(mfcc_features)
                        labels.append(self.genres.index(genre))
                    elif enable_debug:
                        print(f"Skipping file {file_path} due to extraction error")

        if len(features) == 0:
            raise ValueError("No valid features extracted from the dataset")

        features = torch.stack(features)
        labels = torch.tensor(labels)

        if enable_debug:
            print(f"Dataset loaded. Shape of features: {features.shape}, Shape of labels: {labels.shape}")

        return features, labels

    def train_model(self, features, labels, num_genres=10, enable_debug=False):
        if enable_debug:
            start_time = time.time()
            print("Starting model training...")

        train_dataset = MusicGenreDataset(features, labels)
        train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = MusicGenreCNN(num_genres=num_genres).to(device)
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(model.parameters(), lr=0.001)

        num_epochs = 50
        for epoch in range(num_epochs):
            model.train()
            for batch_features, batch_labels in train_loader:
                batch_features, batch_labels = batch_features.to(device), batch_labels.to(device)
                optimizer.zero_grad()
                outputs = model(batch_features)
                loss = criterion(outputs, batch_labels)
                loss.backward()
                optimizer.step()

            if enable_debug and (epoch + 1) % 10 == 0:
                print(f"Epoch [{epoch + 1}/{num_epochs}] completed")

        if enable_debug:
            end_time = time.time()
            print(f"Model training completed. Time taken: {end_time - start_time:.2f} seconds")

        return model

    def predict(self, model, audio_file, enable_debug=False):
        if enable_debug:
            start_time = time.time()
            print("Starting audio prediction...")

        try:
            wav_file = self.convert_to_wav(audio_file)

            target_length = 1291
            n_mfcc = 13

            features = self.extract_features(wav_file, target_length=target_length, n_mfcc=n_mfcc)
            if features is None:
                return "Error: Unable to extract features from the audio file."

            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            model.to(device)

            features = features.unsqueeze(0).to(device)

            with torch.no_grad():
                outputs = model(features)
                probabilities = torch.softmax(outputs, dim=1).cpu().numpy().flatten()

            predicted_probabilities = {genre: prob for genre, prob in zip(self.genres, probabilities)}

            sorted_predicted_probabilities = dict(sorted(predicted_probabilities.items(), key=lambda item: item[1], reverse=True))

            if enable_debug:
                end_time = time.time()
                print(f"Prediction completed. Time taken: {end_time - start_time:.2f} seconds")

        except Exception as e:
            print(str(e))

        finally:
            os.remove(wav_file)

        return sorted_predicted_probabilities

    def save_model(self, model, file_path, enable_debug=False):
        if enable_debug:
            print(f"Saving model to {file_path}...")

        torch.save(model.state_dict(), file_path)

        if enable_debug:
            print(f"Model successfully saved to {file_path}")

    def load_model(self, file_path, num_genres=10, enable_debug=False):
        if enable_debug:
            print(f"Loading model from {file_path}...")

        map_location = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        model = MusicGenreCNN(num_genres=num_genres)
        model.load_state_dict(torch.load(file_path, map_location=map_location, weights_only=True))
        model.eval()

        if enable_debug:
            print("Model loaded successfully")

        return model


def main():
    parser = argparse.ArgumentParser(description="Music Genre Classification")
    parser.add_argument("--dataset", type=str, help="Path to the GTZAN dataset")
    parser.add_argument("--mode", type=str, choices=['train', 'predict'], required=True, help="Mode: train a new model or predict using existing model")
    parser.add_argument("--model_path", type=str, help="Path to save/load the model")
    parser.add_argument("--audio_file", type=str, help="Path to the audio file for prediction")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    classifier = MusicGenresClassifier()

    if args.mode == 'train':
        if args.model_path is None:
            args.model_path = 'music_genre_cnn.pth'

        X, y = classifier.load_dataset(args.dataset, enable_debug=args.debug)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        model = classifier.train_model(X_train, y_train, num_genres=len(classifier.genres), enable_debug=args.debug)
        classifier.save_model(model, args.model_path, enable_debug=args.debug)
        print(f"Model trained and saved to {args.model_path}")

        classifier.save_genres('genres.json')
        print(f"Genres saved to 'genres.json'")

    elif args.mode == 'predict':
        if args.model_path is None or args.audio_file is None:
            parser.error("--model_path and --audio_file are required for prediction mode")

        classifier.load_genres('genres.json')
        model = classifier.load_model(args.model_path, num_genres=len(classifier.genres), enable_debug=args.debug)
        predicted_probabilities = classifier.predict(model, args.audio_file, enable_debug=args.debug)
        for genre, probability in predicted_probabilities.items():
            print(f"{genre}: {probability:.4f}")


if __name__ == "__main__":
    main()