import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigation } from '@react-navigation/native';
import LinearGradient from 'react-native-linear-gradient';
import Icon from 'react-native-vector-icons/MaterialIcons';

import { AppDispatch, RootState } from '../../store/store';
import { verifyEmail, clearError } from '../../store/slices/authSlice';
import { Colors } from '../../constants/Colors';
import { Layout } from '../../constants/Layout';

const EmailVerificationScreen: React.FC = () => {
  const [verificationCode, setVerificationCode] = useState('');
  const [codeError, setCodeError] = useState('');
  const [timeLeft, setTimeLeft] = useState(300); // 5 minutes

  const dispatch = useDispatch<AppDispatch>();
  const navigation = useNavigation();
  const { isLoading, error, user } = useSelector((state: RootState) => state.auth);

  useEffect(() => {
    const timer = setInterval(() => {
      setTimeLeft((prevTime) => {
        if (prevTime <= 1) {
          clearInterval(timer);
          return 0;
        }
        return prevTime - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleVerifyEmail = async () => {
    if (!verificationCode) {
      setCodeError('Verification code is required');
      return;
    }

    if (verificationCode.length < 6) {
      setCodeError('Verification code must be 6 digits');
      return;
    }

    setCodeError('');

    try {
      await dispatch(verifyEmail(verificationCode)).unwrap();
      Alert.alert(
        'Email Verified',
        'Your email has been successfully verified. You can now use all features of the app.',
        [
          {
            text: 'OK',
            onPress: () => navigation.navigate('Login' as never),
          },
        ]
      );
    } catch (error) {
      console.error('Email verification error:', error);
    }
  };

  const handleResendCode = async () => {
    if (timeLeft > 0) {
      Alert.alert(
        'Please Wait',
        `You can request a new code in ${formatTime(timeLeft)}`
      );
      return;
    }

    try {
      // In a real app, you would call an API to resend the verification code
      Alert.alert(
        'Code Sent',
        'A new verification code has been sent to your email.'
      );
      setTimeLeft(300); // Reset timer
    } catch (error) {
      console.error('Resend code error:', error);
    }
  };

  const handleBackToLogin = () => {
    navigation.navigate('Login' as never);
  };

  useEffect(() => {
    if (error) {
      Alert.alert('Verification Failed', error);
      dispatch(clearError());
    }
  }, [error, dispatch]);

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <LinearGradient
        colors={Colors.gradient.primary}
        style={styles.header}
      >
        <TouchableOpacity
          onPress={() => navigation.goBack()}
          style={styles.backButton}
        >
          <Icon name="arrow-back" size={24} color={Colors.primary.contrast} />
        </TouchableOpacity>
        <Text style={styles.title}>Verify Email</Text>
        <Text style={styles.subtitle}>Check your inbox</Text>
      </LinearGradient>

      <View style={styles.formContainer}>
        <View style={styles.emailContainer}>
          <Icon name="email" size={64} color={Colors.primary.main} />
          <Text style={styles.emailText}>
            We've sent a verification code to
          </Text>
          <Text style={styles.emailAddress}>
            {user?.email || 'your email address'}
          </Text>
        </View>

        <View style={styles.instructionContainer}>
          <Text style={styles.instructionText}>
            Enter the 6-digit verification code from your email
          </Text>
        </View>

        <View style={styles.inputContainer}>
          <TextInput
            style={[styles.input, codeError ? styles.inputError : null]}
            placeholder="000000"
            placeholderTextColor={Colors.text.secondary}
            value={verificationCode}
            onChangeText={setVerificationCode}
            keyboardType="numeric"
            maxLength={6}
            autoComplete="one-time-code"
            autoFocus
            textAlign="center"
          />
        </View>
        {codeError ? <Text style={styles.errorText}>{codeError}</Text> : null}

        <TouchableOpacity
          style={styles.verifyButton}
          onPress={handleVerifyEmail}
          disabled={isLoading}
        >
          <LinearGradient
            colors={Colors.gradient.primary}
            style={styles.buttonGradient}
          >
            <Text style={styles.verifyButtonText}>
              {isLoading ? 'Verifying...' : 'Verify Email'}
            </Text>
          </LinearGradient>
        </TouchableOpacity>

        <View style={styles.resendContainer}>
          <Text style={styles.resendText}>Didn't receive the code?</Text>
          <TouchableOpacity
            onPress={handleResendCode}
            disabled={timeLeft > 0}
            style={[styles.resendButton, timeLeft > 0 && styles.disabledButton]}
          >
            <Text style={[
              styles.resendButtonText,
              timeLeft > 0 && styles.disabledButtonText
            ]}>
              {timeLeft > 0 ? `Resend in ${formatTime(timeLeft)}` : 'Resend Code'}
            </Text>
          </TouchableOpacity>
        </View>

        <TouchableOpacity onPress={handleBackToLogin} style={styles.backToLoginButton}>
          <Icon name="arrow-back" size={16} color={Colors.primary.main} />
          <Text style={styles.backToLoginText}>Back to Login</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background.primary,
  },
  header: {
    height: 160,
    justifyContent: 'center',
    alignItems: 'center',
    paddingTop: Layout.statusBarHeight,
  },
  backButton: {
    position: 'absolute',
    top: Layout.statusBarHeight + 10,
    left: 16,
    padding: 8,
  },
  title: {
    fontSize: Layout.fontSize.xxl,
    fontWeight: 'bold',
    color: Colors.primary.contrast,
    marginBottom: Layout.spacing.sm,
  },
  subtitle: {
    fontSize: Layout.fontSize.md,
    color: Colors.primary.contrast,
    opacity: 0.9,
  },
  formContainer: {
    flex: 1,
    padding: Layout.screenPadding,
    paddingTop: Layout.spacing.xl,
  },
  emailContainer: {
    alignItems: 'center',
    marginBottom: Layout.spacing.xl,
  },
  emailText: {
    fontSize: Layout.fontSize.md,
    color: Colors.text.secondary,
    marginTop: Layout.spacing.md,
    textAlign: 'center',
  },
  emailAddress: {
    fontSize: Layout.fontSize.lg,
    color: Colors.text.primary,
    fontWeight: 'bold',
    marginTop: Layout.spacing.sm,
    textAlign: 'center',
  },
  instructionContainer: {
    backgroundColor: Colors.overlay.primary,
    padding: Layout.spacing.md,
    borderRadius: Layout.borderRadius.md,
    marginBottom: Layout.spacing.xl,
  },
  instructionText: {
    fontSize: Layout.fontSize.md,
    color: Colors.text.primary,
    textAlign: 'center',
  },
  inputContainer: {
    marginBottom: Layout.spacing.md,
  },
  input: {
    height: Layout.inputHeight,
    borderWidth: 1,
    borderColor: Colors.border.light,
    borderRadius: Layout.borderRadius.md,
    paddingHorizontal: Layout.spacing.md,
    fontSize: Layout.fontSize.xl,
    color: Colors.text.primary,
    backgroundColor: Colors.background.secondary,
    fontWeight: 'bold',
    letterSpacing: 4,
  },
  inputError: {
    borderColor: Colors.error.main,
  },
  errorText: {
    color: Colors.error.main,
    fontSize: Layout.fontSize.sm,
    marginTop: Layout.spacing.sm,
    textAlign: 'center',
  },
  verifyButton: {
    marginTop: Layout.spacing.xl,
    marginBottom: Layout.spacing.xl,
  },
  buttonGradient: {
    height: Layout.buttonHeight,
    borderRadius: Layout.borderRadius.md,
    justifyContent: 'center',
    alignItems: 'center',
  },
  verifyButtonText: {
    color: Colors.primary.contrast,
    fontSize: Layout.fontSize.lg,
    fontWeight: 'bold',
  },
  resendContainer: {
    alignItems: 'center',
    marginBottom: Layout.spacing.xl,
  },
  resendText: {
    fontSize: Layout.fontSize.md,
    color: Colors.text.secondary,
    marginBottom: Layout.spacing.sm,
  },
  resendButton: {
    padding: Layout.spacing.md,
  },
  resendButtonText: {
    color: Colors.primary.main,
    fontSize: Layout.fontSize.md,
    fontWeight: 'bold',
  },
  disabledButton: {
    opacity: 0.6,
  },
  disabledButtonText: {
    color: Colors.text.secondary,
  },
  backToLoginButton: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 'auto',
    paddingVertical: Layout.spacing.md,
  },
  backToLoginText: {
    color: Colors.primary.main,
    fontSize: Layout.fontSize.md,
    marginLeft: Layout.spacing.sm,
    fontWeight: 'bold',
  },
});

export default EmailVerificationScreen;