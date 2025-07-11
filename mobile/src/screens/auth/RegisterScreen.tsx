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
import { registerUser, clearError } from '../../store/slices/authSlice';
import { Colors } from '../../constants/Colors';
import { Layout } from '../../constants/Layout';

const RegisterScreen: React.FC = () => {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    role: 'student',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [errors, setErrors] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
  });

  const dispatch = useDispatch<AppDispatch>();
  const navigation = useNavigation();
  const { isLoading, error } = useSelector((state: RootState) => state.auth);

  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const validatePassword = (password: string): boolean => {
    return password.length >= 8 && /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(password);
  };

  const validateForm = (): boolean => {
    const newErrors = {
      username: '',
      email: '',
      password: '',
      confirmPassword: '',
    };

    let isValid = true;

    if (!formData.username) {
      newErrors.username = 'Username is required';
      isValid = false;
    } else if (formData.username.length < 3) {
      newErrors.username = 'Username must be at least 3 characters';
      isValid = false;
    }

    if (!formData.email) {
      newErrors.email = 'Email is required';
      isValid = false;
    } else if (!validateEmail(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
      isValid = false;
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
      isValid = false;
    } else if (!validatePassword(formData.password)) {
      newErrors.password = 'Password must be at least 8 characters with uppercase, lowercase, and number';
      isValid = false;
    }

    if (!formData.confirmPassword) {
      newErrors.confirmPassword = 'Please confirm your password';
      isValid = false;
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
      isValid = false;
    }

    setErrors(newErrors);
    return isValid;
  };

  const handleRegister = async () => {
    if (!validateForm()) return;

    try {
      await dispatch(registerUser({
        username: formData.username,
        email: formData.email,
        password: formData.password,
        role: formData.role,
      })).unwrap();
      
      Alert.alert(
        'Registration Successful',
        'Please check your email to verify your account.',
        [
          {
            text: 'OK',
            onPress: () => navigation.navigate('EmailVerification' as never),
          },
        ]
      );
    } catch (error) {
      console.error('Registration error:', error);
    }
  };

  const handleLogin = () => {
    navigation.navigate('Login' as never);
  };

  const updateFormData = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (errors[field as keyof typeof errors]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  useEffect(() => {
    if (error) {
      Alert.alert('Registration Failed', error);
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
          <TouchableOpacity
            onPress={() => navigation.goBack()}
            style={styles.backButton}
          >
            <Icon name="arrow-back" size={24} color={Colors.primary.contrast} />
          </TouchableOpacity>
          <Text style={styles.title}>Create Account</Text>
          <Text style={styles.subtitle}>Join the learning adventure</Text>
        </LinearGradient>

        <View style={styles.formContainer}>
          <View style={styles.inputContainer}>
            <Icon name="person" size={20} color={Colors.text.secondary} style={styles.inputIcon} />
            <TextInput
              style={[styles.input, errors.username ? styles.inputError : null]}
              placeholder="Username"
              placeholderTextColor={Colors.text.secondary}
              value={formData.username}
              onChangeText={(value) => updateFormData('username', value)}
              autoCapitalize="none"
              autoComplete="username"
            />
          </View>
          {errors.username ? <Text style={styles.errorText}>{errors.username}</Text> : null}

          <View style={styles.inputContainer}>
            <Icon name="email" size={20} color={Colors.text.secondary} style={styles.inputIcon} />
            <TextInput
              style={[styles.input, errors.email ? styles.inputError : null]}
              placeholder="Email"
              placeholderTextColor={Colors.text.secondary}
              value={formData.email}
              onChangeText={(value) => updateFormData('email', value)}
              keyboardType="email-address"
              autoCapitalize="none"
              autoComplete="email"
            />
          </View>
          {errors.email ? <Text style={styles.errorText}>{errors.email}</Text> : null}

          <View style={styles.inputContainer}>
            <Icon name="lock" size={20} color={Colors.text.secondary} style={styles.inputIcon} />
            <TextInput
              style={[styles.input, errors.password ? styles.inputError : null]}
              placeholder="Password"
              placeholderTextColor={Colors.text.secondary}
              value={formData.password}
              onChangeText={(value) => updateFormData('password', value)}
              secureTextEntry={!showPassword}
              autoComplete="new-password"
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
          {errors.password ? <Text style={styles.errorText}>{errors.password}</Text> : null}

          <View style={styles.inputContainer}>
            <Icon name="lock" size={20} color={Colors.text.secondary} style={styles.inputIcon} />
            <TextInput
              style={[styles.input, errors.confirmPassword ? styles.inputError : null]}
              placeholder="Confirm Password"
              placeholderTextColor={Colors.text.secondary}
              value={formData.confirmPassword}
              onChangeText={(value) => updateFormData('confirmPassword', value)}
              secureTextEntry={!showConfirmPassword}
              autoComplete="new-password"
            />
            <TouchableOpacity
              onPress={() => setShowConfirmPassword(!showConfirmPassword)}
              style={styles.eyeButton}
            >
              <Icon
                name={showConfirmPassword ? 'visibility' : 'visibility-off'}
                size={20}
                color={Colors.text.secondary}
              />
            </TouchableOpacity>
          </View>
          {errors.confirmPassword ? <Text style={styles.errorText}>{errors.confirmPassword}</Text> : null}

          <View style={styles.roleContainer}>
            <Text style={styles.roleLabel}>I am a:</Text>
            <View style={styles.roleButtons}>
              <TouchableOpacity
                style={[
                  styles.roleButton,
                  formData.role === 'student' && styles.roleButtonActive,
                ]}
                onPress={() => updateFormData('role', 'student')}
              >
                <Text
                  style={[
                    styles.roleButtonText,
                    formData.role === 'student' && styles.roleButtonTextActive,
                  ]}
                >
                  Student
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[
                  styles.roleButton,
                  formData.role === 'teacher' && styles.roleButtonActive,
                ]}
                onPress={() => updateFormData('role', 'teacher')}
              >
                <Text
                  style={[
                    styles.roleButtonText,
                    formData.role === 'teacher' && styles.roleButtonTextActive,
                  ]}
                >
                  Teacher
                </Text>
              </TouchableOpacity>
            </View>
          </View>

          <TouchableOpacity
            style={styles.registerButton}
            onPress={handleRegister}
            disabled={isLoading}
          >
            <LinearGradient
              colors={Colors.gradient.primary}
              style={styles.buttonGradient}
            >
              <Text style={styles.registerButtonText}>
                {isLoading ? 'Creating Account...' : 'Create Account'}
              </Text>
            </LinearGradient>
          </TouchableOpacity>

          <TouchableOpacity onPress={handleLogin} style={styles.loginButton}>
            <Text style={styles.loginText}>Already have an account? </Text>
            <Text style={styles.loginLink}>Sign In</Text>
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
  roleContainer: {
    marginBottom: Layout.spacing.xl,
  },
  roleLabel: {
    fontSize: Layout.fontSize.md,
    color: Colors.text.primary,
    marginBottom: Layout.spacing.md,
    fontWeight: '600',
  },
  roleButtons: {
    flexDirection: 'row',
    gap: Layout.spacing.md,
  },
  roleButton: {
    flex: 1,
    padding: Layout.spacing.md,
    borderWidth: 1,
    borderColor: Colors.border.light,
    borderRadius: Layout.borderRadius.md,
    alignItems: 'center',
    backgroundColor: Colors.background.secondary,
  },
  roleButtonActive: {
    borderColor: Colors.primary.main,
    backgroundColor: Colors.overlay.primary,
  },
  roleButtonText: {
    fontSize: Layout.fontSize.md,
    color: Colors.text.secondary,
  },
  roleButtonTextActive: {
    color: Colors.primary.main,
    fontWeight: 'bold',
  },
  registerButton: {
    marginBottom: Layout.spacing.xl,
  },
  buttonGradient: {
    height: Layout.buttonHeight,
    borderRadius: Layout.borderRadius.md,
    justifyContent: 'center',
    alignItems: 'center',
  },
  registerButtonText: {
    color: Colors.primary.contrast,
    fontSize: Layout.fontSize.lg,
    fontWeight: 'bold',
  },
  loginButton: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
  },
  loginText: {
    color: Colors.text.secondary,
    fontSize: Layout.fontSize.md,
  },
  loginLink: {
    color: Colors.primary.main,
    fontSize: Layout.fontSize.md,
    fontWeight: 'bold',
  },
});

export default RegisterScreen;