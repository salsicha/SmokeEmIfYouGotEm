#include "RaftSimInputContracts.h"

#include "RaftSimInputActions.h"

namespace
{
FRaftSimManualInputActionContract MakeInputContract(
    FName ActionId,
    FName DeterministicIntent,
    ERaftSimInputValueType ValueType,
    ERaftSimInputGameplayMode GameplayMode,
    bool bGuidedPaddleVoiceEligible
)
{
    FRaftSimManualInputActionContract Contract;
    Contract.ActionId = ActionId;
    Contract.DeterministicIntent = DeterministicIntent;
    Contract.ValueType = ValueType;
    Contract.GameplayMode = GameplayMode;
    Contract.bGuidedPaddleVoiceEligible = bGuidedPaddleVoiceEligible;
    return Contract;
}
}

TArray<FRaftSimManualInputActionContract> URaftSimInputContractLibrary::GetMilestone23ManualInputContracts()
{
    return {
        MakeInputContract(
            RaftSimInputActions::PaddleStroke,
            TEXT("guide_paddle_stroke"),
            ERaftSimInputValueType::Axis3D,
            ERaftSimInputGameplayMode::GuidedPaddleRaft,
            false
        ),
        MakeInputContract(
            RaftSimInputActions::PaddleBrace,
            TEXT("guide_brace"),
            ERaftSimInputValueType::Boolean,
            ERaftSimInputGameplayMode::SharedSafety,
            true
        ),
        MakeInputContract(
            RaftSimInputActions::PaddleDraw,
            TEXT("guide_draw_or_rudder"),
            ERaftSimInputValueType::Axis2D,
            ERaftSimInputGameplayMode::GuidedPaddleRaft,
            false
        ),
        MakeInputContract(
            RaftSimInputActions::OarLeftStroke,
            TEXT("rowing_left_oar_stroke"),
            ERaftSimInputValueType::Axis2D,
            ERaftSimInputGameplayMode::RowingOarRig,
            false
        ),
        MakeInputContract(
            RaftSimInputActions::OarRightStroke,
            TEXT("rowing_right_oar_stroke"),
            ERaftSimInputValueType::Axis2D,
            ERaftSimInputGameplayMode::RowingOarRig,
            false
        ),
        MakeInputContract(
            RaftSimInputActions::OarFeather,
            TEXT("rowing_oar_feather"),
            ERaftSimInputValueType::Axis1D,
            ERaftSimInputGameplayMode::RowingOarRig,
            false
        ),
        MakeInputContract(
            RaftSimInputActions::GuideCommandForwardPaddle,
            TEXT("crew_forward_paddle"),
            ERaftSimInputValueType::Boolean,
            ERaftSimInputGameplayMode::GuidedPaddleRaft,
            true
        ),
        MakeInputContract(
            RaftSimInputActions::GuideCommandBackPaddle,
            TEXT("crew_back_paddle"),
            ERaftSimInputValueType::Boolean,
            ERaftSimInputGameplayMode::GuidedPaddleRaft,
            true
        ),
        MakeInputContract(
            RaftSimInputActions::GuideCommandLeftPaddle,
            TEXT("crew_left_paddle"),
            ERaftSimInputValueType::Boolean,
            ERaftSimInputGameplayMode::GuidedPaddleRaft,
            true
        ),
        MakeInputContract(
            RaftSimInputActions::GuideCommandRightPaddle,
            TEXT("crew_right_paddle"),
            ERaftSimInputValueType::Boolean,
            ERaftSimInputGameplayMode::GuidedPaddleRaft,
            true
        ),
        MakeInputContract(
            RaftSimInputActions::GuideCommandStop,
            TEXT("crew_stop"),
            ERaftSimInputValueType::Boolean,
            ERaftSimInputGameplayMode::GuidedPaddleRaft,
            true
        ),
        MakeInputContract(
            RaftSimInputActions::HighSide,
            TEXT("crew_high_side"),
            ERaftSimInputValueType::Boolean,
            ERaftSimInputGameplayMode::SharedSafety,
            true
        ),
        MakeInputContract(
            RaftSimInputActions::CrewLean,
            TEXT("crew_lean_lateral"),
            ERaftSimInputValueType::Axis1D,
            ERaftSimInputGameplayMode::SharedSafety,
            false
        ),
        MakeInputContract(
            RaftSimInputActions::HoldOn,
            TEXT("crew_hold_on"),
            ERaftSimInputValueType::Boolean,
            ERaftSimInputGameplayMode::SharedSafety,
            true
        ),
        MakeInputContract(
            RaftSimInputActions::RescueTargetSelect,
            TEXT("rescue_target_select"),
            ERaftSimInputValueType::Axis1D,
            ERaftSimInputGameplayMode::SharedSafety,
            false
        ),
        MakeInputContract(
            RaftSimInputActions::RescueReachGrab,
            TEXT("rescue_reach_or_paddle_grab"),
            ERaftSimInputValueType::Boolean,
            ERaftSimInputGameplayMode::SharedSafety,
            false
        ),
        MakeInputContract(
            RaftSimInputActions::RescueThrowLine,
            TEXT("rescue_throw_line"),
            ERaftSimInputValueType::Boolean,
            ERaftSimInputGameplayMode::SharedSafety,
            false
        ),
        MakeInputContract(
            RaftSimInputActions::ReseatCrew,
            TEXT("crew_reseat_recovery"),
            ERaftSimInputValueType::Boolean,
            ERaftSimInputGameplayMode::SharedSafety,
            true
        ),
        MakeInputContract(
            RaftSimInputActions::GuideCommandPushToTalk,
            TEXT("voice_command_gate"),
            ERaftSimInputValueType::Boolean,
            ERaftSimInputGameplayMode::GuidedPaddleRaft,
            false
        ),
        MakeInputContract(
            RaftSimInputActions::RecenterVR,
            TEXT("recenter_guide_camera"),
            ERaftSimInputValueType::Boolean,
            ERaftSimInputGameplayMode::SharedSafety,
            false
        )
    };
}

bool URaftSimInputContractLibrary::HasManualParity(const FRaftSimManualInputActionContract& Contract)
{
    return Contract.bKeyboardMouse && Contract.bGamepad && Contract.bVRMotionControllers;
}

bool URaftSimInputContractLibrary::IsEnabledForGameplayMode(
    const FRaftSimManualInputActionContract& Contract,
    ERaftSimInputGameplayMode GameplayMode
)
{
    return Contract.GameplayMode == ERaftSimInputGameplayMode::SharedSafety
        || Contract.GameplayMode == GameplayMode;
}

bool URaftSimInputContractLibrary::CanRouteFromVoiceInGuidedPaddleRaft(
    const FRaftSimManualInputActionContract& Contract
)
{
    return Contract.bGuidedPaddleVoiceEligible
        && Contract.GameplayMode != ERaftSimInputGameplayMode::RowingOarRig;
}
