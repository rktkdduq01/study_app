import React from 'react';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import LinearGradient from 'react-native-linear-gradient';
import { Colors } from '../../constants/Colors';
import { Layout } from '../../constants/Layout';

const LoadingScreen: React.FC = () => {
  return (
    <LinearGradient
      colors={Colors.gradient.primary}
      style={styles.container}
    >
      <View style={styles.content}>
        <Text style={styles.title}>Educational RPG</Text>
        <Text style={styles.subtitle}>Learn, Play, Grow</Text>
        <ActivityIndicator 
          size="large" 
          color={Colors.primary.contrast}
          style={styles.loader}
        />
        <Text style={styles.loadingText}>Loading...</Text>
      </View>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  content: {
    alignItems: 'center',
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
    marginBottom: Layout.spacing.xl,
  },
  loader: {
    marginBottom: Layout.spacing.lg,
  },
  loadingText: {
    fontSize: Layout.fontSize.md,
    color: Colors.primary.contrast,
    opacity: 0.8,
  },
});

export default LoadingScreen;