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
import torchaudio.transforms as T
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from torch.utils.data import Dataset, DataLoader
from pydub import AudioSegment


class MusicGenreDataset(Dataset):
    """
    Custom dataset class for loading music genre data.
    """
    def __init__(self, X, y):
        self.X = torch.FloatTensor(X)
        self.y = torch.LongTensor(y)

    def __len__(self):
        return len(self.y)

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]


class MusicGenreCNN(nn.Module):
    """
    Convolutional Neural Network model for music genre classification.
    """
    def __init__(self, num_genres, input_length=1291, n_mfcc=20):  # Use the same input_length as target_length in extract_features
        super(MusicGenreCNN, self).__init__()
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, stride=1, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1)
        self.pool = nn.MaxPool2d(2, 2)
        self.dropout = nn.Dropout(0.5)

        # Calculate flattened size dynamically based on input length
        example_input = torch.zeros(1, 1, n_mfcc, input_length)
        conv_output = self._forward_conv(example_input)
        self.flattened_size = conv_output.view(1, -1).size(1)

        # Initialize fully connected layers
        self.fc1 = nn.Linear(self.flattened_size, 128)
        self.fc2 = nn.Linear(128, num_genres)
        self.dropout_fc = nn.Dropout(0.5)  # Additional dropout for the FC layer

    def _forward_conv(self, x):
        """
        Forward pass through convolutional layers.
        """
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        return x

    def forward(self, x):
        """
        Forward pass through the entire network.
        """
        x = self._forward_conv(x)
        x = x.view(x.size(0), -1)
        x = self.dropout_fc(F.relu(self.fc1(x)))
        x = self.fc2(x)
        return x


class MusicGenresClassifier:
    """
    Classifier class for training and predicting music genres.
    """
    def __init__(self, num_genres, target_length=1291, n_mfcc=20):
        self.genres = []
        self.target_length = target_length
        self.n_mfcc=n_mfcc
        self.model = MusicGenreCNN(
            input_length=self.target_length,
            n_mfcc=self.n_mfcc,
            num_genres=num_genres)

    def save_genres(self, file_path):
        """
        Save the list of genres to a file.
        """
        with open(file_path, 'w') as f:
            json.dump(self.genres, f)

    def load_genres(self, file_path):
        """
        Load the list of genres from a file.
        """
        with open(file_path, 'r') as f:
            self.genres = json.load(f)

    def convert_to_wav(self, audio_file):
        """
        Convert audio files to WAV format.
        """
        temp_dir = os.path.join(os.getcwd(), "temp")
        os.makedirs(temp_dir, exist_ok=True)

        audio = AudioSegment.from_file(audio_file)
        audio = audio.set_frame_rate(44100).set_channels(1).set_sample_width(2)

        wav_file_path = os.path.join(temp_dir, os.path.basename(audio_file).replace(os.path.splitext(audio_file)[-1], '.wav'))
        audio.export(wav_file_path, format="wav")

        return wav_file_path

    def inspect_audio(self, file_path):
        """
        Print audio information.
        """
        info = torchaudio.info(file_path)
        print(info)

    def process_waveform(self, waveform, sample_rate, target_sample_rate=44100, num_channels=1):
        """
        Resample the waveform and adjust the number of channels.
        """
        if sample_rate != target_sample_rate:
            resample_transform = T.Resample(orig_freq=sample_rate, new_freq=target_sample_rate)
            waveform = resample_transform(waveform)

        # Convert to mono if num_channels is 1
        if waveform.shape[0] > 1 and num_channels == 1:
            waveform = torch.mean(waveform, dim=0, keepdim=True)
        elif waveform.shape[0] == 1 and num_channels > 1:
            waveform = waveform.repeat(num_channels, 1)

        return waveform, target_sample_rate

    def extract_features(self, waveform=None, file_path=None, duration=None):
        """
        Extracts MFCC features from the waveform or file.

        Args:
            waveform (torch.Tensor, optional): Audio waveform tensor.
            file_path (str, optional): Path to the audio file.
            duration (float, optional): Duration to truncate the audio to.
            n_mfcc (int): Number of MFCC features to extract.

        Returns:
            torch.Tensor: Extracted MFCC features tensor.
        """
        try:
            if waveform is None and file_path is not None:
                waveform, sr = torchaudio.load(file_path)
            elif waveform is not None:
                sr = 44100
            else:
                raise ValueError("Either waveform or file_path must be provided")

            # Normalize waveform
            waveform = waveform / waveform.abs().max()
            waveform, sr = self.process_waveform(waveform, sr)

            # Data augmentation: Add noise
            noise = torch.randn(waveform.size()) * 0.005
            waveform = waveform + noise

            # Extract MFCC features
            mfcc_transform = torchaudio.transforms.MFCC(
                sample_rate=sr,
                n_mfcc=self.n_mfcc,
                melkwargs={'n_mels': 64, 'n_fft': 2048}
            )
            mfcc = mfcc_transform(waveform)

            # Ensure MFCC dimensions are correct
            if mfcc.dim() == 2:
                mfcc = mfcc.unsqueeze(0)  # Add a channel dimension
            # Ensure consistent feature length
            target_length = self.target_length
            
            # Ensure feature length consistency
            current_length = mfcc.shape[-1]
            if current_length < target_length:
                pad_size = target_length - current_length
                mfcc = F.pad(mfcc, (0, pad_size), "constant", 0)
            elif current_length > target_length:
                mfcc = mfcc[:, :, :target_length]

            return mfcc

        except Exception as e:
            print(f"Error processing waveform or file {file_path}: {str(e)}")
            traceback.print_exc()
            return None

    def load_dataset(self, dataset_path, enable_debug=False):
        self.genres = ['blues', 'classical', 'country', 'disco', 'hiphop', 'jazz', 'metal', 'pop', 'reggae', 'rock']
        features = []
        labels = []

        if enable_debug:
            print("Starting to load dataset...")
            
        for genre in self.genres:
            genre_path = os.path.join(dataset_path, genre)
            for file in os.listdir(genre_path):
                if file.endswith('.wav'):
                    file_path = os.path.join(genre_path, file)
                    mfcc_features = self.extract_features(file_path=file_path)
                    if mfcc_features is not None:
                        features.append(mfcc_features)
                        labels.append(self.genres.index(genre))
                    elif enable_debug:
                        print(f"Skipping file {file_path} due to extraction error")

        if len(features) == 0:
            raise ValueError("No valid features extracted from the dataset")

        # Ensure all features have the same length
        features = torch.stack(features)
        labels = torch.tensor(labels)

        if enable_debug:
            print(f"Dataset loaded. Shape of features: {features.shape}, Shape of labels: {labels.shape}")

        return features, labels

    def train_model(self, features, labels, num_genres=10, enable_debug=False):
        """
        Train the model using the provided features and labels.
        """
        if enable_debug:
            start_time = time.time()
            print("Starting model training...")

        # Split the data into training and validation sets
        X_train, X_val, y_train, y_val = train_test_split(features, labels, test_size=0.1, random_state=42)

        train_dataset = MusicGenreDataset(X_train, y_train)
        val_dataset = MusicGenreDataset(X_val, y_val)

        train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False)

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = self.model.to(device)
        criterion = nn.CrossEntropyLoss()
        
        # Initialize optimizer with weight decay (L2 regularization)
        optimizer = optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-4)  # Add weight_decay for L2 regularization

        num_epochs = 50
        train_losses, val_losses = [], []
        best_val_loss = float('inf')

        for epoch in range(num_epochs):
            model.train()
            epoch_train_loss = 0.0
            
            for batch_features, batch_labels in train_loader:
                batch_features, batch_labels = batch_features.to(device), batch_labels.to(device)
                optimizer.zero_grad()
                outputs = model(batch_features)
                loss = criterion(outputs, batch_labels)
                loss.backward()
                optimizer.step()
                epoch_train_loss += loss.item()

            train_losses.append(epoch_train_loss / len(train_loader))

            # Validation phase
            model.eval()
            epoch_val_loss = 0.0
            with torch.no_grad():
                for batch_features, batch_labels in val_loader:
                    batch_features, batch_labels = batch_features.to(device), batch_labels.to(device)
                    outputs = model(batch_features)
                    loss = criterion(outputs, batch_labels)
                    epoch_val_loss += loss.item()

            val_losses.append(epoch_val_loss / len(val_loader))

            if epoch_val_loss < best_val_loss:
                best_val_loss = epoch_val_loss

            if enable_debug and (epoch + 1) % 10 == 0:
                print(f"Epoch [{epoch + 1}/{num_epochs}] completed, Training Loss: {epoch_train_loss / len(train_loader):.4f}, Validation Loss: {epoch_val_loss / len(val_loader):.4f}")

        if enable_debug:
            end_time = time.time()
            print(f"Model training completed. Time taken: {end_time - start_time:.2f} seconds")

        # Plot training and validation loss
        plt.plot(train_losses, label='Training loss')
        plt.plot(val_losses, label='Validation loss')
        plt.legend()
        
        # Save the plot as a file
        plt.savefig('training_validation_loss.png')
        print("Training and validation loss plot saved as 'training_validation_loss.png'")

        return model

    def predict(self, model, waveform, enable_debug=False):
        """
        Predict the genre of a given audio waveform.
        """
        if enable_debug:
            start_time = time.time()
            print("Starting audio prediction...")

        try:
            # Ensure the waveform is correctly formatted
            if waveform.dim() == 3:  # If input is (batch_size, 1, time)
                waveform = waveform.squeeze(1)  # Remove the channel dimension for processing

            features = self.extract_features(waveform=waveform)
            if features is None:
                return "Error: Unable to extract features from the audio waveform."

            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            model.to(device)

            features = features.unsqueeze(0).to(device)  # Add batch dimension

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
            sorted_predicted_probabilities = None  # Assign to prevent UnboundLocalError

        return sorted_predicted_probabilities

    def save_model(self, model, file_path, enable_debug=False):
        """
        Save the trained model to a file.
        """
        if enable_debug:
            print(f"Saving model to {file_path}...")

        torch.save(model.state_dict(), file_path)

        if enable_debug:
            print(f"Model successfully saved to {file_path}")

    def load_model(self, file_path, num_genres=10, enable_debug=False):
        """
        Load a pre-trained model from a file.
        """
        if enable_debug:
            print(f"Loading model from {file_path}...")

        map_location = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        self.model = MusicGenreCNN(num_genres=num_genres)
        self.model.load_state_dict(torch.load(file_path, map_location=map_location), strict=False)
        self.model.eval()

        if enable_debug:
            print("Model loaded successfully")

        return self.model


def main():
    parser = argparse.ArgumentParser(description="Music Genre Classification")
    parser.add_argument("--dataset", type=str, help="Path to the GTZAN dataset")
    parser.add_argument("--mode", type=str, choices=['train', 'predict'], required=True, help="Mode: train a new model or predict using existing model")
    parser.add_argument("--model_path", type=str, help="Path to save/load the model")
    parser.add_argument("--audio_file", type=str, help="Path to the audio file for prediction")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    num_genres = 10
    classifier = MusicGenresClassifier(num_genres=num_genres)

    if args.mode == 'train':
        if args.model_path is None:
            args.model_path = 'music_genre_cnn.pth'

        X, y = classifier.load_dataset(args.dataset, enable_debug=args.debug)
        model = classifier.train_model(X, y, enable_debug=args.debug)
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