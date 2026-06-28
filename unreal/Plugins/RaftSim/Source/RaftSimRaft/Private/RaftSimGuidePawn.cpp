#include "RaftSimGuidePawn.h"

#include "Camera/CameraComponent.h"
#include "Components/SceneComponent.h"

ARaftSimGuidePawn::ARaftSimGuidePawn()
{
    PrimaryActorTick.bCanEverTick = true;

    Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
    SetRootComponent(Root);

    GuideSeatAnchor = CreateDefaultSubobject<USceneComponent>(TEXT("GuideSeatAnchor"));
    GuideSeatAnchor->SetupAttachment(Root);
    GuideSeatAnchor->SetRelativeLocation(FVector(-180.0f, 0.0f, 45.0f));

    PaddleAnchor = CreateDefaultSubobject<USceneComponent>(TEXT("PaddleAnchor"));
    PaddleAnchor->SetupAttachment(GuideSeatAnchor);
    PaddleAnchor->SetRelativeLocation(FVector(25.0f, -65.0f, -20.0f));

    GuideCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("GuideCamera"));
    GuideCamera->SetupAttachment(GuideSeatAnchor);
    GuideCamera->SetRelativeLocation(FVector::ZeroVector);
    GuideCamera->bUsePawnControlRotation = true;
}
