#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "AbilitySystemInterface.h"
#include "GameplayTagContainer.h"
#include "BaseCharacter.generated.h"

class UAbilitySystemComponent;
class UMyAttributeSet;
class UGameplayEffect;
class UGameplayAbility;
class UPrimitiveComponent;
class USpringArmComponent;
class UCameraComponent;
struct FGameplayTag;

UCLASS()
class PROJECTUNREAL_API ABaseCharacter : public ACharacter, public IAbilitySystemInterface
{
	GENERATED_BODY()

public:
	ABaseCharacter();

	virtual UAbilitySystemComponent* GetAbilitySystemComponent() const override;

protected:
	virtual void BeginPlay() override;

	// ---- 纯动词:只执行,不含政策。策略(什么时候吞/什么时候收刀)在 BP 事件图里组合 ----
	UFUNCTION(BlueprintCallable, Category = "Combat")
	void RequestAttack();

	UFUNCTION(BlueprintCallable, Category = "Combat")
	void CancelAttack();

	UFUNCTION(BlueprintCallable, Category = "Combat")
	void RequestJump();

	UFUNCTION(BlueprintCallable, Category = "Input")
	void Move2D(const FVector2D Axis);

	UFUNCTION(BlueprintCallable, Category = "Input")
	void Look2D(const FVector2D Axis);

	// ---- 纯查询:供 BP 策略分支读取 ----
	UFUNCTION(BlueprintPure, Category = "Combat")
	bool IsMoveLocked() const;

	UFUNCTION(BlueprintPure, Category = "Combat")
	bool IsAttacking() const;

	// UI 数据接口:血/体力百分比(UMG ProgressBar 绑定用)。纯查询。
	UFUNCTION(BlueprintPure, Category = "Attributes")
	float GetHealthPercent() const;

	UFUNCTION(BlueprintPure, Category = "Attributes")
	float GetStaminaPercent() const;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "GAS")
	TObjectPtr<UAbilitySystemComponent> AbilitySystemComponent;

	UPROPERTY()
	TObjectPtr<const UMyAttributeSet> AttributeSet;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "GAS")
	TSubclassOf<UGameplayEffect> InitAttributesEffect;

	// 语义闸门读的标签:策划可在 BP 里改指,默认 = 项目现行标签体系
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "GAS|Tags")
	FGameplayTag MoveLockedTag;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "GAS|Tags")
	FGameplayTag AttackingTag;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "GAS|Tags")
	FGameplayTag AttackAbilityTag;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "GAS|Tags")
	FGameplayTag AttackHitEventTag;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Camera")
	TObjectPtr<USpringArmComponent> CameraBoom;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Camera")
	TObjectPtr<UCameraComponent> FollowCamera;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "GAS")
	TArray<TSubclassOf<UGameplayAbility>> StartupAbilities;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Camera")
	float DefaultCameraPitch = -15.f;

	UFUNCTION(BlueprintCallable, Category = "Combat")
	void RegisterWeaponCollision(UPrimitiveComponent* Comp);

	UFUNCTION(BlueprintCallable, Category = "Combat")
	void SetWeaponCollisionEnabled(bool bEnabled);

	UFUNCTION()
	void OnWeaponOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult);

	UPROPERTY()
	TObjectPtr<UPrimitiveComponent> WeaponCollisionComp;

	UPROPERTY()
	TSet<TObjectPtr<AActor>> HitActorsThisSwing;

private:
	// 标签属性为空(注册前创建的 CDO)时回退到现行标签
	static FGameplayTag ResolveTag(const FGameplayTag& Tag, const TCHAR* Fallback);
};
