import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Alert,
  Modal,
  TextInput,
} from 'react-native';
import { useDispatch, useSelector } from 'react-redux';
import LinearGradient from 'react-native-linear-gradient';
import Icon from 'react-native-vector-icons/MaterialIcons';

import { AppDispatch, RootState } from '../../store/store';
import {
  fetchCharacter,
  createCharacter,
  updateCharacterStats,
  levelUp,
  setLevelUpAnimation,
} from '../../store/slices/characterSlice';
import { Colors } from '../../constants/Colors';
import { Layout } from '../../constants/Layout';

const CharacterScreen: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { character, stats, isLoading, levelUpAnimation } = useSelector(
    (state: RootState) => state.character
  );
  const { user } = useSelector((state: RootState) => state.auth);

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [characterName, setCharacterName] = useState('');
  const [selectedClass, setSelectedClass] = useState('warrior');

  useEffect(() => {
    dispatch(fetchCharacter());
  }, [dispatch]);

  useEffect(() => {
    if (levelUpAnimation) {
      setTimeout(() => {
        dispatch(setLevelUpAnimation(false));
      }, 3000);
    }
  }, [levelUpAnimation, dispatch]);

  const handleCreateCharacter = async () => {
    if (!characterName.trim()) {
      Alert.alert('Error', 'Please enter a character name');
      return;
    }

    try {
      await dispatch(createCharacter({
        character_class: selectedClass,
        name: characterName,
        appearance: { theme: selectedClass },
      })).unwrap();
      setShowCreateModal(false);
      setCharacterName('');
    } catch (error) {
      Alert.alert('Error', 'Failed to create character');
    }
  };

  const handleLevelUp = async () => {
    try {
      await dispatch(levelUp()).unwrap();
      Alert.alert('Level Up!', 'Congratulations! You have leveled up!');
    } catch (error) {
      Alert.alert('Error', 'Failed to level up');
    }
  };

  const handleStatIncrease = async (stat: string) => {
    if (!character || character.available_stat_points <= 0) return;

    try {
      await dispatch(updateCharacterStats({
        [stat]: (stats as any)[stat] + 1,
      })).unwrap();
    } catch (error) {
      Alert.alert('Error', 'Failed to update stats');
    }
  };

  const characterClasses = [
    { id: 'warrior', name: 'Warrior', description: 'Strong melee fighter', color: Colors.character.warrior },
    { id: 'mage', name: 'Mage', description: 'Magical spell caster', color: Colors.character.mage },
    { id: 'archer', name: 'Archer', description: 'Skilled ranged attacker', color: Colors.character.archer },
    { id: 'scholar', name: 'Scholar', description: 'Wise knowledge seeker', color: Colors.character.scholar },
  ];

  const getClassColor = (className: string) => {
    const classInfo = characterClasses.find(c => c.id === className);
    return classInfo ? classInfo.color : Colors.primary.main;
  };

  const canLevelUp = character && character.experience >= (character.level * 100);

  if (!character) {
    return (
      <View style={styles.container}>
        <View style={styles.noCharacterContainer}>
          <Icon name="person-add" size={64} color={Colors.primary.main} />
          <Text style={styles.noCharacterTitle}>Create Your Character</Text>
          <Text style={styles.noCharacterText}>
            Start your learning adventure by creating your character!
          </Text>
          <TouchableOpacity
            style={styles.createButton}
            onPress={() => setShowCreateModal(true)}
          >
            <LinearGradient
              colors={Colors.gradient.primary}
              style={styles.buttonGradient}
            >
              <Text style={styles.createButtonText}>Create Character</Text>
            </LinearGradient>
          </TouchableOpacity>
        </View>

        <Modal
          visible={showCreateModal}
          transparent
          animationType="slide"
          onRequestClose={() => setShowCreateModal(false)}
        >
          <View style={styles.modalOverlay}>
            <View style={styles.modalContent}>
              <Text style={styles.modalTitle}>Create Character</Text>
              
              <TextInput
                style={styles.nameInput}
                placeholder="Enter character name"
                value={characterName}
                onChangeText={setCharacterName}
                autoFocus
              />

              <Text style={styles.classLabel}>Choose Your Class</Text>
              <View style={styles.classGrid}>
                {characterClasses.map((cls) => (
                  <TouchableOpacity
                    key={cls.id}
                    style={[
                      styles.classCard,
                      selectedClass === cls.id && styles.selectedClass,
                      { borderColor: cls.color },
                    ]}
                    onPress={() => setSelectedClass(cls.id)}
                  >
                    <Text style={[styles.className, { color: cls.color }]}>
                      {cls.name}
                    </Text>
                    <Text style={styles.classDescription}>
                      {cls.description}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>

              <View style={styles.modalButtons}>
                <TouchableOpacity
                  style={[styles.modalButton, styles.cancelButton]}
                  onPress={() => setShowCreateModal(false)}
                >
                  <Text style={styles.cancelButtonText}>Cancel</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.modalButton, styles.confirmButton]}
                  onPress={handleCreateCharacter}
                >
                  <Text style={styles.confirmButtonText}>Create</Text>
                </TouchableOpacity>
              </View>
            </View>
          </View>
        </Modal>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      {levelUpAnimation && (
        <View style={styles.levelUpOverlay}>
          <Text style={styles.levelUpText}>LEVEL UP!</Text>
          <Text style={styles.levelUpSubtext}>Level {character.level}</Text>
        </View>
      )}

      <LinearGradient
        colors={[getClassColor(character.character_class), Colors.background.primary]}
        style={styles.header}
      >
        <View style={styles.characterInfo}>
          <Text style={styles.characterName}>{character.name}</Text>
          <Text style={styles.characterClass}>
            Level {character.level} {character.character_class}
          </Text>
        </View>
        
        <View style={styles.experienceContainer}>
          <Text style={styles.experienceLabel}>Experience</Text>
          <View style={styles.experienceBar}>
            <View
              style={[
                styles.experienceFill,
                { width: `${(character.experience / (character.level * 100)) * 100}%` },
              ]}
            />
          </View>
          <Text style={styles.experienceText}>
            {character.experience}/{character.level * 100}
          </Text>
        </View>

        {canLevelUp && (
          <TouchableOpacity
            style={styles.levelUpButton}
            onPress={handleLevelUp}
          >
            <Text style={styles.levelUpButtonText}>Level Up!</Text>
          </TouchableOpacity>
        )}
      </LinearGradient>

      <View style={styles.content}>
        {/* Stats */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Stats</Text>
          {character.available_stat_points > 0 && (
            <Text style={styles.statPointsText}>
              Available Points: {character.available_stat_points}
            </Text>
          )}
          
          {stats && (
            <View style={styles.statsGrid}>
              {Object.entries(stats).map(([key, value]) => {
                if (key.startsWith('max_') || key === 'id' || key === 'user_id') return null;
                
                return (
                  <View key={key} style={styles.statItem}>
                    <Text style={styles.statName}>
                      {key.replace('_', ' ').toUpperCase()}
                    </Text>
                    <Text style={styles.statValue}>{value}</Text>
                    {character.available_stat_points > 0 && (
                      <TouchableOpacity
                        style={styles.statButton}
                        onPress={() => handleStatIncrease(key)}
                      >
                        <Icon name="add" size={16} color={Colors.primary.contrast} />
                      </TouchableOpacity>
                    )}
                  </View>
                );
              })}
            </View>
          )}
        </View>

        {/* Health and Mana */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Vitals</Text>
          
          <View style={styles.vitalItem}>
            <View style={styles.vitalHeader}>
              <Text style={styles.vitalLabel}>Health</Text>
              <Text style={styles.vitalValue}>
                {stats?.health}/{stats?.max_health}
              </Text>
            </View>
            <View style={styles.vitalBar}>
              <View
                style={[
                  styles.vitalFill,
                  { 
                    width: `${stats ? (stats.health / stats.max_health) * 100 : 0}%`,
                    backgroundColor: Colors.rpg.health,
                  },
                ]}
              />
            </View>
          </View>

          <View style={styles.vitalItem}>
            <View style={styles.vitalHeader}>
              <Text style={styles.vitalLabel}>Mana</Text>
              <Text style={styles.vitalValue}>
                {stats?.mana}/{stats?.max_mana}
              </Text>
            </View>
            <View style={styles.vitalBar}>
              <View
                style={[
                  styles.vitalFill,
                  { 
                    width: `${stats ? (stats.mana / stats.max_mana) * 100 : 0}%`,
                    backgroundColor: Colors.rpg.mana,
                  },
                ]}
              />
            </View>
          </View>
        </View>

        {/* Equipment */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Equipment</Text>
          <View style={styles.equipmentGrid}>
            <View style={styles.equipmentSlot}>
              <Text style={styles.equipmentLabel}>Weapon</Text>
              <View style={styles.equipmentItem}>
                <Icon name="sports-martial-arts" size={24} color={Colors.text.secondary} />
              </View>
            </View>
            <View style={styles.equipmentSlot}>
              <Text style={styles.equipmentLabel}>Armor</Text>
              <View style={styles.equipmentItem}>
                <Icon name="shield" size={24} color={Colors.text.secondary} />
              </View>
            </View>
            <View style={styles.equipmentSlot}>
              <Text style={styles.equipmentLabel}>Accessory</Text>
              <View style={styles.equipmentItem}>
                <Icon name="auto-awesome" size={24} color={Colors.text.secondary} />
              </View>
            </View>
          </View>
        </View>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background.primary,
  },
  noCharacterContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: Layout.screenPadding,
  },
  noCharacterTitle: {
    fontSize: Layout.fontSize.xl,
    fontWeight: 'bold',
    color: Colors.text.primary,
    marginTop: Layout.spacing.lg,
    marginBottom: Layout.spacing.md,
  },
  noCharacterText: {
    fontSize: Layout.fontSize.md,
    color: Colors.text.secondary,
    textAlign: 'center',
    marginBottom: Layout.spacing.xl,
  },
  createButton: {
    width: '100%',
  },
  buttonGradient: {
    height: Layout.buttonHeight,
    borderRadius: Layout.borderRadius.md,
    justifyContent: 'center',
    alignItems: 'center',
  },
  createButtonText: {
    color: Colors.primary.contrast,
    fontSize: Layout.fontSize.lg,
    fontWeight: 'bold',
  },
  header: {
    padding: Layout.screenPadding,
    paddingTop: Layout.spacing.xl,
  },
  characterInfo: {
    alignItems: 'center',
    marginBottom: Layout.spacing.lg,
  },
  characterName: {
    fontSize: Layout.fontSize.xxl,
    fontWeight: 'bold',
    color: Colors.primary.contrast,
  },
  characterClass: {
    fontSize: Layout.fontSize.md,
    color: Colors.primary.contrast,
    opacity: 0.9,
  },
  experienceContainer: {
    marginBottom: Layout.spacing.md,
  },
  experienceLabel: {
    fontSize: Layout.fontSize.sm,
    color: Colors.primary.contrast,
    marginBottom: Layout.spacing.xs,
  },
  experienceBar: {
    height: 8,
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
    borderRadius: Layout.borderRadius.xs,
    overflow: 'hidden',
  },
  experienceFill: {
    height: '100%',
    backgroundColor: Colors.rpg.experience,
  },
  experienceText: {
    fontSize: Layout.fontSize.sm,
    color: Colors.primary.contrast,
    textAlign: 'center',
    marginTop: Layout.spacing.xs,
  },
  levelUpButton: {
    backgroundColor: Colors.success.main,
    padding: Layout.spacing.md,
    borderRadius: Layout.borderRadius.md,
    alignItems: 'center',
  },
  levelUpButtonText: {
    color: Colors.success.contrast,
    fontSize: Layout.fontSize.md,
    fontWeight: 'bold',
  },
  levelUpOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000,
  },
  levelUpText: {
    fontSize: Layout.fontSize.xxxl,
    fontWeight: 'bold',
    color: Colors.rpg.gold,
    textShadowColor: 'rgba(0, 0, 0, 0.5)',
    textShadowOffset: { width: 2, height: 2 },
    textShadowRadius: 4,
  },
  levelUpSubtext: {
    fontSize: Layout.fontSize.lg,
    color: Colors.primary.contrast,
    marginTop: Layout.spacing.md,
  },
  content: {
    padding: Layout.screenPadding,
  },
  card: {
    backgroundColor: Colors.background.secondary,
    borderRadius: Layout.borderRadius.md,
    padding: Layout.cardPadding,
    marginBottom: Layout.spacing.lg,
    ...Layout.shadow,
  },
  cardTitle: {
    fontSize: Layout.fontSize.lg,
    fontWeight: 'bold',
    color: Colors.text.primary,
    marginBottom: Layout.spacing.md,
  },
  statPointsText: {
    fontSize: Layout.fontSize.sm,
    color: Colors.warning.main,
    marginBottom: Layout.spacing.md,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: Layout.spacing.md,
  },
  statItem: {
    flex: 1,
    minWidth: '45%',
    backgroundColor: Colors.background.tertiary,
    padding: Layout.spacing.md,
    borderRadius: Layout.borderRadius.sm,
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  statName: {
    fontSize: Layout.fontSize.sm,
    color: Colors.text.secondary,
  },
  statValue: {
    fontSize: Layout.fontSize.lg,
    fontWeight: 'bold',
    color: Colors.text.primary,
  },
  statButton: {
    backgroundColor: Colors.primary.main,
    width: 24,
    height: 24,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  vitalItem: {
    marginBottom: Layout.spacing.md,
  },
  vitalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Layout.spacing.xs,
  },
  vitalLabel: {
    fontSize: Layout.fontSize.md,
    color: Colors.text.primary,
  },
  vitalValue: {
    fontSize: Layout.fontSize.md,
    fontWeight: 'bold',
    color: Colors.text.primary,
  },
  vitalBar: {
    height: 12,
    backgroundColor: Colors.border.light,
    borderRadius: Layout.borderRadius.sm,
    overflow: 'hidden',
  },
  vitalFill: {
    height: '100%',
    borderRadius: Layout.borderRadius.sm,
  },
  equipmentGrid: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  equipmentSlot: {
    alignItems: 'center',
  },
  equipmentLabel: {
    fontSize: Layout.fontSize.sm,
    color: Colors.text.secondary,
    marginBottom: Layout.spacing.xs,
  },
  equipmentItem: {
    width: 60,
    height: 60,
    backgroundColor: Colors.background.tertiary,
    borderRadius: Layout.borderRadius.sm,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: Colors.border.light,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    backgroundColor: Colors.background.secondary,
    borderRadius: Layout.borderRadius.md,
    padding: Layout.spacing.lg,
    width: '90%',
    maxWidth: 400,
  },
  modalTitle: {
    fontSize: Layout.fontSize.lg,
    fontWeight: 'bold',
    color: Colors.text.primary,
    textAlign: 'center',
    marginBottom: Layout.spacing.lg,
  },
  nameInput: {
    borderWidth: 1,
    borderColor: Colors.border.light,
    borderRadius: Layout.borderRadius.sm,
    padding: Layout.spacing.md,
    fontSize: Layout.fontSize.md,
    marginBottom: Layout.spacing.lg,
  },
  classLabel: {
    fontSize: Layout.fontSize.md,
    fontWeight: 'bold',
    color: Colors.text.primary,
    marginBottom: Layout.spacing.md,
  },
  classGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: Layout.spacing.md,
    marginBottom: Layout.spacing.lg,
  },
  classCard: {
    flex: 1,
    minWidth: '45%',
    borderWidth: 2,
    borderRadius: Layout.borderRadius.sm,
    padding: Layout.spacing.md,
    alignItems: 'center',
  },
  selectedClass: {
    backgroundColor: Colors.overlay.primary,
  },
  className: {
    fontSize: Layout.fontSize.md,
    fontWeight: 'bold',
    marginBottom: Layout.spacing.xs,
  },
  classDescription: {
    fontSize: Layout.fontSize.sm,
    color: Colors.text.secondary,
    textAlign: 'center',
  },
  modalButtons: {
    flexDirection: 'row',
    gap: Layout.spacing.md,
  },
  modalButton: {
    flex: 1,
    padding: Layout.spacing.md,
    borderRadius: Layout.borderRadius.sm,
    alignItems: 'center',
  },
  cancelButton: {
    backgroundColor: Colors.background.tertiary,
  },
  confirmButton: {
    backgroundColor: Colors.primary.main,
  },
  cancelButtonText: {
    color: Colors.text.primary,
    fontSize: Layout.fontSize.md,
  },
  confirmButtonText: {
    color: Colors.primary.contrast,
    fontSize: Layout.fontSize.md,
    fontWeight: 'bold',
  },
});

export default CharacterScreen;