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
  ScrollView,
} from 'react-native';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigation } from '@react-navigation/native';
import LinearGradient from 'react-native-linear-gradient';
import Icon from 'react-native-vector-icons/MaterialIcons';

import { AppDispatch, RootState } from '../../store/store';
import { loginUser, clearError, checkLockStatus } from '../../store/slices/authSlice';
import { Colors } from '../../constants/Colors';
import { Layout } from '../../constants/Layout';

const LoginScreen: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [emailError, setEmailError] = useState('');
  const [passwordError, setPasswordError] = useState('');

  const dispatch = useDispatch<AppDispatch>();
  const navigation = useNavigation();
  const { isLoading, error, isLocked, lockUntil, loginAttempts } = useSelector(
    (state: RootState) => state.auth
  );

  useEffect(() => {
    dispatch(checkLockStatus());
  }, [dispatch]);

  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const validateForm = (): boolean => {
    let isValid = true;
    
    if (!email) {
      setEmailError('Email is required');
      isValid = false;
    } else if (!validateEmail(email)) {
      setEmailError('Please enter a valid email address');
      isValid = false;
    } else {
      setEmailError('');
    }

    if (!password) {
      setPasswordError('Password is required');
      isValid = false;
    } else if (password.length < 6) {
      setPasswordError('Password must be at least 6 characters');
      isValid = false;
    } else {
      setPasswordError('');
    }

    return isValid;
  };

  const handleLogin = async () => {
    if (!validateForm()) return;

    if (isLocked) {
      const remainingTime = lockUntil ? Math.ceil((lockUntil - Date.now()) / 60000) : 0;
      Alert.alert(
        'Account Locked',
        `Too many failed attempts. Please try again in ${remainingTime} minutes.`
      );
      return;
    }

    try {
      await dispatch(loginUser({ email, password })).unwrap();
    } catch (error) {
      console.error('Login error:', error);
    }
  };

  const handleForgotPassword = () => {
    navigation.navigate('ForgotPassword' as never);
  };

  const handleRegister = () => {
    navigation.navigate('Register' as never);
  };

  const getRemainingTime = (): string => {
    if (!lockUntil) return '';
    const remaining = Math.ceil((lockUntil - Date.now()) / 60000);
    return `${remaining} minute${remaining !== 1 ? 's' : ''}`;
  };

  useEffect(() => {
    if (error) {
      Alert.alert('Login Failed', error);
      dispatch(clearError());
    }
  }, [error, dispatch]);

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView contentContainerStyle={styles.scrollContainer}>
        <LinearGradient
          colors={Colors.gradient.primary}
          style={styles.header}
        >
          <Text style={styles.title}>Educational RPG</Text>
          <Text style={styles.subtitle}>Learn, Play, Grow</Text>
        </LinearGradient>

        <View style={styles.formContainer}>
          <Text style={styles.welcomeText}>Welcome Back!</Text>
          
          {isLocked && (
            <View style={styles.lockNotice}>
              <Icon name="lock" size={20} color={Colors.error.main} />
              <Text style={styles.lockText}>
                Account locked. Try again in {getRemainingTime()}
              </Text>
            </View>
          )}

          {loginAttempts > 0 && !isLocked && (
            <View style={styles.attemptWarning}>
              <Text style={styles.attemptText}>
                {5 - loginAttempts} attempts remaining
              </Text>
            </View>
          )}

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
            />
          </View>
          {emailError ? <Text style={styles.errorText}>{emailError}</Text> : null}

          <View style={styles.inputContainer}>
            <Icon name="lock" size={20} color={Colors.text.secondary} style={styles.inputIcon} />
            <TextInput
              style={[styles.input, passwordError ? styles.inputError : null]}
              placeholder="Password"
              placeholderTextColor={Colors.text.secondary}
              value={password}
              onChangeText={setPassword}
              secureTextEntry={!showPassword}
              autoComplete="password"
            />
            <TouchableOpacity
              onPress={() => setShowPassword(!showPassword)}
              style={styles.eyeButton}
            >
              <Icon
                name={showPassword ? 'visibility' : 'visibility-off'}
                size={20}
                color={Colors.text.secondary}
              />
            </TouchableOpacity>
          </View>
          {passwordError ? <Text style={styles.errorText}>{passwordError}</Text> : null}

          <TouchableOpacity onPress={handleForgotPassword} style={styles.forgotButton}>
            <Text style={styles.forgotText}>Forgot Password?</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.loginButton, isLocked && styles.disabledButton]}
            onPress={handleLogin}
            disabled={isLoading || isLocked}
          >
            <LinearGradient
              colors={isLocked ? [Colors.border.main, Colors.border.dark] : Colors.gradient.primary}
              style={styles.buttonGradient}
            >
              <Text style={styles.loginButtonText}>
                {isLoading ? 'Logging in...' : 'Login'}
              </Text>
            </LinearGradient>
          </TouchableOpacity>

          <View style={styles.divider}>
            <View style={styles.dividerLine} />
            <Text style={styles.dividerText}>OR</Text>
            <View style={styles.dividerLine} />
          </View>

          <TouchableOpacity onPress={handleRegister} style={styles.registerButton}>
            <Text style={styles.registerText}>Don't have an account? </Text>
            <Text style={styles.registerLink}>Sign Up</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background.primary,
  },
  scrollContainer: {
    flexGrow: 1,
  },
  header: {
    height: 200,
    justifyContent: 'center',
    alignItems: 'center',
    paddingTop: Layout.statusBarHeight,
  },
  title: {
    fontSize: Layout.fontSize.xxxl,
    fontWeight: 'bold',
    color: Colors.primary.contrast,
    marginBottom: Layout.spacing.sm,
  },
  subtitle: {
    fontSize: Layout.fontSize.lg,
    color: Colors.primary.contrast,
    opacity: 0.9,
  },
  formContainer: {
    flex: 1,
    padding: Layout.screenPadding,
    paddingTop: Layout.spacing.xl,
  },
  welcomeText: {
    fontSize: Layout.fontSize.xxl,
    fontWeight: 'bold',
    color: Colors.text.primary,
    textAlign: 'center',
    marginBottom: Layout.spacing.xl,
  },
  lockNotice: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.overlay.error,
    padding: Layout.spacing.md,
    borderRadius: Layout.borderRadius.sm,
    marginBottom: Layout.spacing.md,
  },
  lockText: {
    color: Colors.error.main,
    marginLeft: Layout.spacing.sm,
    fontSize: Layout.fontSize.sm,
  },
  attemptWarning: {
    backgroundColor: Colors.overlay.warning,
    padding: Layout.spacing.sm,
    borderRadius: Layout.borderRadius.sm,
    marginBottom: Layout.spacing.md,
  },
  attemptText: {
    color: Colors.warning.main,
    fontSize: Layout.fontSize.sm,
    textAlign: 'center',
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
  eyeButton: {
    padding: Layout.spacing.md,
  },
  errorText: {
    color: Colors.error.main,
    fontSize: Layout.fontSize.sm,
    marginTop: -Layout.spacing.sm,
    marginBottom: Layout.spacing.md,
    marginLeft: Layout.spacing.sm,
  },
  forgotButton: {
    alignSelf: 'flex-end',
    marginBottom: Layout.spacing.xl,
  },
  forgotText: {
    color: Colors.primary.main,
    fontSize: Layout.fontSize.sm,
  },
  loginButton: {
    marginBottom: Layout.spacing.xl,
  },
  disabledButton: {
    opacity: 0.6,
  },
  buttonGradient: {
    height: Layout.buttonHeight,
    borderRadius: Layout.borderRadius.md,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loginButtonText: {
    color: Colors.primary.contrast,
    fontSize: Layout.fontSize.lg,
    fontWeight: 'bold',
  },
  divider: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: Layout.spacing.xl,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: Colors.border.light,
  },
  dividerText: {
    marginHorizontal: Layout.spacing.md,
    color: Colors.text.secondary,
    fontSize: Layout.fontSize.sm,
  },
  registerButton: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
  },
  registerText: {
    color: Colors.text.secondary,
    fontSize: Layout.fontSize.md,
  },
  registerLink: {
    color: Colors.primary.main,
    fontSize: Layout.fontSize.md,
    fontWeight: 'bold',
  },
});

export default LoginScreen;