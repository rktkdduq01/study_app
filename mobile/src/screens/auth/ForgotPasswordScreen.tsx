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
import { resetPassword, clearError } from '../../store/slices/authSlice';
import { Colors } from '../../constants/Colors';
import { Layout } from '../../constants/Layout';

const ForgotPasswordScreen: React.FC = () => {
  const [email, setEmail] = useState('');
  const [emailError, setEmailError] = useState('');
  const [isEmailSent, setIsEmailSent] = useState(false);

  const dispatch = useDispatch<AppDispatch>();
  const navigation = useNavigation();
  const { isLoading, error } = useSelector((state: RootState) => state.auth);

  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const handleResetPassword = async () => {
    if (!email) {
      setEmailError('Email is required');
      return;
    }

    if (!validateEmail(email)) {
      setEmailError('Please enter a valid email address');
      return;
    }

    setEmailError('');

    try {
      await dispatch(resetPassword(email)).unwrap();
      setIsEmailSent(true);
      Alert.alert(
        'Reset Email Sent',
        'Please check your email for password reset instructions.',
        [
          {
            text: 'OK',
            onPress: () => navigation.navigate('Login' as never),
          },
        ]
      );
    } catch (error) {
      console.error('Reset password error:', error);
    }
  };

  const handleBackToLogin = () => {
    navigation.navigate('Login' as never);
  };

  useEffect(() => {
    if (error) {
      Alert.alert('Reset Failed', error);
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
        <Text style={styles.title}>Reset Password</Text>
        <Text style={styles.subtitle}>We'll send you a reset link</Text>
      </LinearGradient>

      <View style={styles.formContainer}>
        {!isEmailSent ? (
          <>
            <View style={styles.instructionContainer}>
              <Icon name="info" size={24} color={Colors.primary.main} />
              <Text style={styles.instructionText}>
                Enter your email address and we'll send you a link to reset your password.
              </Text>
            </View>

            <View style={styles.inputContainer}>
              <Icon name="email" size={20} color={Colors.text.secondary} style={styles.inputIcon} />
              <TextInput
                style={[styles.input, emailError ? styles.inputError : null]}
                placeholder="Email"
                placeholderTextColor={Colors.text.secondary}
                value={email}
                onChangeText={setEmail}
                keyboardType="email-address"
                autoCapitalize="none"
                autoComplete="email"
                autoFocus
              />
            </View>
            {emailError ? <Text style={styles.errorText}>{emailError}</Text> : null}

            <TouchableOpacity
              style={styles.resetButton}
              onPress={handleResetPassword}
              disabled={isLoading}
            >
              <LinearGradient
                colors={Colors.gradient.primary}
                style={styles.buttonGradient}
              >
                <Text style={styles.resetButtonText}>
                  {isLoading ? 'Sending...' : 'Send Reset Link'}
                </Text>
              </LinearGradient>
            </TouchableOpacity>
          </>
        ) : (
          <View style={styles.successContainer}>
            <View style={styles.successIcon}>
              <Icon name="check-circle" size={64} color={Colors.success.main} />
            </View>
            <Text style={styles.successTitle}>Email Sent!</Text>
            <Text style={styles.successMessage}>
              We've sent a password reset link to {email}. Please check your email and follow the instructions to reset your password.
            </Text>
            <Text style={styles.successNote}>
              Didn't receive the email? Check your spam folder or try again.
            </Text>
            
            <TouchableOpacity
              style={styles.resendButton}
              onPress={() => setIsEmailSent(false)}
            >
              <Text style={styles.resendButtonText}>Try Again</Text>
            </TouchableOpacity>
          </View>
        )}

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
  instructionContainer: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: Colors.overlay.primary,
    padding: Layout.spacing.md,
    borderRadius: Layout.borderRadius.md,
    marginBottom: Layout.spacing.xl,
  },
  instructionText: {
    flex: 1,
    marginLeft: Layout.spacing.md,
    fontSize: Layout.fontSize.md,
    color: Colors.text.primary,
    lineHeight: 20,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.border.light,
    borderRadius: Layout.borderRadius.md,
    marginBottom: Layout.spacing.md,
    backgroundColor: Colors.background.secondary,
  },
  inputIcon: {
    marginLeft: Layout.spacing.md,
  },
  input: {
    flex: 1,
    height: Layout.inputHeight,
    paddingHorizontal: Layout.spacing.md,
    fontSize: Layout.fontSize.md,
    color: Colors.text.primary,
  },
  inputError: {
    borderColor: Colors.error.main,
  },
  errorText: {
    color: Colors.error.main,
    fontSize: Layout.fontSize.sm,
    marginTop: -Layout.spacing.sm,
    marginBottom: Layout.spacing.md,
    marginLeft: Layout.spacing.sm,
  },
  resetButton: {
    marginTop: Layout.spacing.xl,
    marginBottom: Layout.spacing.xl,
  },
  buttonGradient: {
    height: Layout.buttonHeight,
    borderRadius: Layout.borderRadius.md,
    justifyContent: 'center',
    alignItems: 'center',
  },
  resetButtonText: {
    color: Colors.primary.contrast,
    fontSize: Layout.fontSize.lg,
    fontWeight: 'bold',
  },
  successContainer: {
    alignItems: 'center',
    paddingVertical: Layout.spacing.xl,
  },
  successIcon: {
    marginBottom: Layout.spacing.lg,
  },
  successTitle: {
    fontSize: Layout.fontSize.xl,
    fontWeight: 'bold',
    color: Colors.success.main,
    marginBottom: Layout.spacing.md,
  },
  successMessage: {
    fontSize: Layout.fontSize.md,
    color: Colors.text.primary,
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: Layout.spacing.md,
  },
  successNote: {
    fontSize: Layout.fontSize.sm,
    color: Colors.text.secondary,
    textAlign: 'center',
    marginBottom: Layout.spacing.xl,
  },
  resendButton: {
    padding: Layout.spacing.md,
  },
  resendButtonText: {
    color: Colors.primary.main,
    fontSize: Layout.fontSize.md,
    fontWeight: 'bold',
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

export default ForgotPasswordScreen;