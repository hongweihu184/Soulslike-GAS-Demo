#include "BaseCharacter.h"
#include "AbilitySystemComponent.h"
#include "MyAttributeSet.h"
#include "GameFramework/SpringArmComponent.h"
#include "Camera/CameraComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Abilities/GameplayAbility.h"
#include "GameplayTagContainer.h"
#include "Components/PrimitiveComponent.h"
#include "AbilitySystemBlueprintLibrary.h"

ABaseCharacter::ABaseCharacter()
{
	PrimaryActorTick.bCanEverTick = false;

	AbilitySystemComponent = CreateDefaultSubobject<UAbilitySystemComponent>(TEXT("AbilitySystemComponent"));
	AttributeSet = CreateDefaultSubobject<UMyAttributeSet>(TEXT("AttributeSet"));

	CameraBoom = CreateDefaultSubobject<USpringArmComponent>(TEXT("CameraBoom"));
	CameraBoom->SetupAttachment(RootComponent);
	CameraBoom->TargetArmLength = 400.f;
	CameraBoom->bUsePawnControlRotation = true;

	FollowCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("FollowCamera"));
	FollowCamera->SetupAttachment(CameraBoom, USpringArmComponent::SocketName);
	FollowCamera->bUsePawnControlRotation = false;

	bUseControllerRotationYaw = false;
	GetCharacterMovement()->bOrientRotationToMovement = true;
	GetCharacterMovement()->RotationRate = FRotator(0.f, 540.f, 0.f);

	// 默认标签(CDO 创建时若标签未注册则为空,BeginPlay 里有回退解析)
	MoveLockedTag = FGameplayTag::RequestGameplayTag(TEXT("State.MoveLocked"));
	AttackingTag = FGameplayTag::RequestGameplayTag(TEXT("State.Attacking"));
	AttackAbilityTag = FGameplayTag::RequestGameplayTag(TEXT("Ability.Attack.Light"));
	AttackHitEventTag = FGameplayTag::RequestGameplayTag(TEXT("Event.Montage.Attack.Hit"));
}

FGameplayTag ABaseCharacter::ResolveTag(const FGameplayTag& Tag, const TCHAR* Fallback)
{
	return Tag.IsValid() ? Tag : FGameplayTag::RequestGameplayTag(FName(Fallback));
}

UAbilitySystemComponent* ABaseCharacter::GetAbilitySystemComponent() const
{
	return AbilitySystemComponent;
}

void ABaseCharacter::BeginPlay()
{
	Super::BeginPlay();

	MoveLockedTag = ResolveTag(MoveLockedTag, TEXT("State.MoveLocked"));
	AttackingTag = ResolveTag(AttackingTag, TEXT("State.Attacking"));
	AttackAbilityTag = ResolveTag(AttackAbilityTag, TEXT("Ability.Attack.Light"));
	AttackHitEventTag = ResolveTag(AttackHitEventTag, TEXT("Event.Montage.Attack.Hit"));

	if (AController* C = GetController())
	{
		FRotator ControlRot = C->GetControlRotation();
		ControlRot.Pitch = DefaultCameraPitch;
		C->SetControlRotation(ControlRot);
	}

	if (AbilitySystemComponent && InitAttributesEffect)
	{
		FGameplayEffectContextHandle Context = AbilitySystemComponent->MakeEffectContext();
		Context.AddSourceObject(this);

		const FGameplayEffectSpecHandle Spec = AbilitySystemComponent->MakeOutgoingSpec(InitAttributesEffect, 1.f, Context);
		if (Spec.IsValid())
		{
			AbilitySystemComponent->ApplyGameplayEffectSpecToSelf(*Spec.Data.Get());
		}
	}

	if (AbilitySystemComponent)
	{
		for (const TSubclassOf<UGameplayAbility>& AbilityClass : StartupAbilities)
		{
			if (AbilityClass)
			{
				AbilitySystemComponent->GiveAbility(FGameplayAbilitySpec(AbilityClass, 1, -1, this));
			}
		}
	}
}

void ABaseCharacter::RequestAttack()
{
	if (AbilitySystemComponent)
	{
		AbilitySystemComponent->TryActivateAbilitiesByTag(FGameplayTagContainer(AttackAbilityTag));
	}
}

void ABaseCharacter::RequestJump()
{
	Jump();
}

void ABaseCharacter::CancelAttack()
{
	if (AbilitySystemComponent)
	{
		const FGameplayTagContainer AttackTags(AttackAbilityTag);
		AbilitySystemComponent->CancelAbilities(&AttackTags);
	}
}

bool ABaseCharacter::IsMoveLocked() const
{
	return AbilitySystemComponent && AbilitySystemComponent->HasMatchingGameplayTag(MoveLockedTag);
}

bool ABaseCharacter::IsAttacking() const
{
	return AbilitySystemComponent && AbilitySystemComponent->HasMatchingGameplayTag(AttackingTag);
}

void ABaseCharacter::RegisterWeaponCollision(UPrimitiveComponent* Comp)
{
	WeaponCollisionComp = Comp;
	if (!WeaponCollisionComp)
	{
		UE_LOG(LogTemp, Warning, TEXT("[武器碰撞] 注册失败:Comp 为空"));
		return;
	}

	WeaponCollisionComp->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	WeaponCollisionComp->SetCollisionObjectType(ECC_WorldDynamic);
	WeaponCollisionComp->SetCollisionResponseToAllChannels(ECR_Ignore);
	WeaponCollisionComp->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
	WeaponCollisionComp->OnComponentBeginOverlap.AddDynamic(this, &ABaseCharacter::OnWeaponOverlap);

	UE_LOG(LogTemp, Warning, TEXT("[武器碰撞] 注册成功:%s"), *WeaponCollisionComp->GetName());
}

void ABaseCharacter::SetWeaponCollisionEnabled(bool bEnabled)
{
	UE_LOG(LogTemp, Warning, TEXT("[武器碰撞] 开关=%d,已注册=%s"), bEnabled ? 1 : 0, WeaponCollisionComp ? TEXT("是") : TEXT("否"));

	if (!WeaponCollisionComp)
	{
		return;
	}

	if (bEnabled)
	{
		HitActorsThisSwing.Empty();
		WeaponCollisionComp->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	}
	else
	{
		WeaponCollisionComp->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	}
}

void ABaseCharacter::OnWeaponOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
	if (!OtherActor || OtherActor == this || HitActorsThisSwing.Contains(OtherActor))
	{
		return;
	}
	HitActorsThisSwing.Add(OtherActor);

	UE_LOG(LogTemp, Warning, TEXT("[武器碰撞] 命中:%s"), *OtherActor->GetName());

	FGameplayEventData Payload;
	Payload.Instigator = this;
	Payload.Target = OtherActor;
	Payload.TargetData = UAbilitySystemBlueprintLibrary::AbilityTargetDataFromActor(OtherActor);
	UAbilitySystemBlueprintLibrary::SendGameplayEventToActor(this, AttackHitEventTag, Payload);
}

void ABaseCharacter::Move2D(const FVector2D Axis)
{
	// 纯移动动词:锁吞输入/收刀策略已迁到 BP_Player 事件图(读 IsMoveLocked/IsAttacking/HasAttackLockApplied 组合)
	if (!Controller)
	{
		return;
	}

	const FRotator YawRotation(0.f, Controller->GetControlRotation().Yaw, 0.f);
	const FVector Forward = FRotationMatrix(YawRotation).GetUnitAxis(EAxis::X);
	const FVector Right = FRotationMatrix(YawRotation).GetUnitAxis(EAxis::Y);

	AddMovementInput(Forward, Axis.Y);
	AddMovementInput(Right, Axis.X);
}

void ABaseCharacter::Look2D(const FVector2D Axis)
{
	AddControllerYawInput(Axis.X);
	AddControllerPitchInput(Axis.Y);
}

