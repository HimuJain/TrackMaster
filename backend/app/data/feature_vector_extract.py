import os
import json
import numpy as np
import torch
import torchaudio
import librosa
from pathlib import Path
from torch import nn
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from tqdm import tqdm

class AudioFeatureExtractor:
    """
    Extract advanced audio features including timbre and spectrogram analysis
    for improved genre classification.
    """
    
    def __init__(self, sample_rate=22050, n_fft=2048, hop_length=512, n_mels=128, 
                 n_mfcc=20, duration=30.0):
        """
        Initialize the feature extractor.
        
        Parameters:
        -----------
        sample_rate : int
            Sample rate to use for analysis
        n_fft : int
            FFT window size
        hop_length : int
            Hop length for FFT
        n_mels : int
            Number of Mel bands
        n_mfcc : int
            Number of MFCCs to extract
        duration : float
            Duration in seconds to analyze (for fixed-length features)
        """
        self.sample_rate = sample_rate
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.n_mels = n_mels
        self.n_mfcc = n_mfcc
        self.duration = duration
        
        # Calculate fixed-length dimensions
        self.fixed_length = int(duration * sample_rate)
        self.n_frames = 1 + int((self.fixed_length - n_fft) / hop_length)
    
    def extract_features(self, audio, sr):
        """
        Extract comprehensive audio features.
        
        Parameters:
        -----------
        audio : numpy.ndarray
            Audio signal
        sr : int
            Sample rate of the audio
            
        Returns:
        --------
        features : dict
            Dictionary containing various audio features
        """
        # Resample if necessary
        if sr != self.sample_rate:
            audio = librosa.resample(audio, orig_sr=sr, target_sr=self.sample_rate)
        
        # Ensure consistent length
        if len(audio) < self.fixed_length:
            # Pad if too short
            audio = np.pad(audio, (0, self.fixed_length - len(audio)))
        elif len(audio) > self.fixed_length:
            # Trim if too long
            audio = audio[:self.fixed_length]
        
        # --- Spectral Features ---
        
        # Mel spectrogram
        mel_spec = librosa.feature.melspectrogram(
            y=audio, 
            sr=self.sample_rate,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
            n_mels=self.n_mels
        )
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
        
        # MFCCs
        mfccs = librosa.feature.mfcc(
            y=audio, 
            sr=self.sample_rate, 
            n_mfcc=self.n_mfcc,
            n_fft=self.n_fft,
            hop_length=self.hop_length
        )
        delta_mfccs = librosa.feature.delta(mfccs)
        delta2_mfccs = librosa.feature.delta(mfccs, order=2)
        
        # --- Timbre Features ---
        
        # Spectral centroid (brightness)
        spectral_centroid = librosa.feature.spectral_centroid(
            y=audio, 
            sr=self.sample_rate,
            n_fft=self.n_fft,
            hop_length=self.hop_length
        )
        
        # Spectral bandwidth (spread)
        spectral_bandwidth = librosa.feature.spectral_bandwidth(
            y=audio, 
            sr=self.sample_rate,
            n_fft=self.n_fft,
            hop_length=self.hop_length
        )
        
        # Spectral flatness (noisiness vs. tonalness)
        spectral_flatness = librosa.feature.spectral_flatness(
            y=audio,
            n_fft=self.n_fft,
            hop_length=self.hop_length
        )
        
        # Spectral contrast
        spectral_contrast = librosa.feature.spectral_contrast(
            y=audio, 
            sr=self.sample_rate,
            n_fft=self.n_fft,
            hop_length=self.hop_length
        )
        
        # Spectral rolloff
        spectral_rolloff = librosa.feature.spectral_rolloff(
            y=audio, 
            sr=self.sample_rate,
            n_fft=self.n_fft,
            hop_length=self.hop_length
        )
        
        # Zero crossing rate (related to perception of noisiness)
        zero_crossing_rate = librosa.feature.zero_crossing_rate(
            y=audio,
            frame_length=self.n_fft,
            hop_length=self.hop_length
        )
        
        # --- Rhythmic Features ---
        
        # Tempogram
        oenv = librosa.onset.onset_strength(
            y=audio, 
            sr=self.sample_rate,
            hop_length=self.hop_length
        )
        tempogram = librosa.feature.tempogram(
            onset_envelope=oenv, 
            sr=self.sample_rate,
            hop_length=self.hop_length
        )
        
        # Tempo and beat information
        tempo, _ = librosa.beat.beat_track(
            onset_envelope=oenv, 
            sr=self.sample_rate,
            hop_length=self.hop_length
        )
        
        # --- Harmonic and Tonal Features ---
        
        # Chroma features
        chroma = librosa.feature.chroma_stft(
            y=audio, 
            sr=self.sample_rate,
            n_fft=self.n_fft,
            hop_length=self.hop_length
        )
        
        # Harmonic-percussive source separation
        harmonic, percussive = librosa.effects.hpss(audio)
        
        # Tonnetz (tonal centroid features)
        tonnetz = librosa.feature.tonnetz(
            y=harmonic, 
            sr=self.sample_rate
        )
        
        # --- Statistical Features ---
        # Compute statistics for each feature to create fixed-length vectors
        
        # Create feature dictionary
        features = {
            'mel_spectrogram': mel_spec_db,
            'mfcc': {
                'mean': np.mean(mfccs, axis=1),
                'std': np.std(mfccs, axis=1),
            },
            'timbre': {
                'centroid_mean': np.mean(spectral_centroid),
                'centroid_std': np.std(spectral_centroid),
                'bandwidth_mean': np.mean(spectral_bandwidth),
                'bandwidth_std': np.std(spectral_bandwidth),
                'flatness_mean': np.mean(spectral_flatness),
                'flatness_std': np.std(spectral_flatness),
                'contrast_mean': np.mean(spectral_contrast, axis=1),
                'rolloff_mean': np.mean(spectral_rolloff),
                'zcr_mean': np.mean(zero_crossing_rate),
                'zcr_std': np.std(zero_crossing_rate)
            },
            'rhythm': {
                'tempo': tempo,
                'tempogram_mean': np.mean(tempogram, axis=1)
            },
            'tonal': {
                'chroma_mean': np.mean(chroma, axis=1),
                'tonnetz_mean': np.mean(tonnetz, axis=1)
            }
        }
        
        return self.create_feature_vector(features)
    
    def create_feature_vector(self, features):
        """
        Create a flat feature vector from the feature dictionary.
        
        Parameters:
        -----------
        features : dict
            Dictionary of audio features
            
        Returns:
        --------
        feature_vector : numpy.ndarray
            Flat feature vector combining all relevant features
        """
        # Combine all statistical features
        vectors = [
            features['mfcc']['mean'],
            features['mfcc']['std'],
            np.array([features['timbre']['centroid_mean']]),
            np.array([features['timbre']['centroid_std']]),
            np.array([features['timbre']['bandwidth_mean']]),
            np.array([features['timbre']['bandwidth_std']]),
            np.array([features['timbre']['flatness_mean']]),
            np.array([features['timbre']['flatness_std']]),
            features['timbre']['contrast_mean'],
            np.array([features['timbre']['rolloff_mean']]),
            np.array([features['timbre']['zcr_mean']]),
            np.array([features['timbre']['zcr_std']]),
            np.array([features['rhythm']['tempo']]),
            features['rhythm']['tempogram_mean'],
            features['tonal']['chroma_mean'],
            features['tonal']['tonnetz_mean']
        ]
        
        # Concatenate all vectors
        feature_vector = np.concatenate([v.flatten() for v in vectors])
        print(len(feature_vector))
        
        return feature_vector