#include "RaftSimReplayDebugViewer.h"

#include "Math/UnrealMathUtility.h"

void URaftSimReplayDebugViewerViewModel::Configure(URaftSimReplayDebugViewerConfig* InConfig)
{
    Config = InConfig;
    PlaybackTimeSeconds = 0.0f;
    CurrentBookmarkId = NAME_None;
    OverlayStates.Reset();

    if (!Config)
    {
        return;
    }

    for (const FRaftSimReplayDebugOverlayToggle& Overlay : Config->Overlays)
    {
        OverlayStates.Add(Overlay.View, Overlay.bDefaultEnabled);
    }

    if (!Config->Bookmarks.IsEmpty())
    {
        CurrentBookmarkId = Config->Bookmarks[0].BookmarkId;
        PlaybackTimeSeconds = Config->Bookmarks[0].TimeSeconds;
    }
}

bool URaftSimReplayDebugViewerViewModel::SetPlaybackTime(float InTimeSeconds)
{
    if (!Config)
    {
        return false;
    }

    PlaybackTimeSeconds = FMath::Clamp(InTimeSeconds, 0.0f, GetMaxPlaybackTimeSeconds());
    CurrentBookmarkId = NAME_None;
    return true;
}

bool URaftSimReplayDebugViewerViewModel::JumpToBookmark(FName BookmarkId)
{
    if (const FRaftSimReplayDebugBookmark* Bookmark = FindBookmark(BookmarkId))
    {
        PlaybackTimeSeconds = FMath::Clamp(Bookmark->TimeSeconds, 0.0f, GetMaxPlaybackTimeSeconds());
        CurrentBookmarkId = Bookmark->BookmarkId;
        return true;
    }

    return false;
}

void URaftSimReplayDebugViewerViewModel::SetOverlayEnabled(ERaftSimWaterDebugView View, bool bEnabled)
{
    OverlayStates.Add(View, bEnabled);
}

bool URaftSimReplayDebugViewerViewModel::IsOverlayEnabled(ERaftSimWaterDebugView View) const
{
    if (const bool* bEnabled = OverlayStates.Find(View))
    {
        return *bEnabled;
    }

    return false;
}

const FRaftSimReplayDebugBookmark* URaftSimReplayDebugViewerViewModel::FindBookmark(FName BookmarkId) const
{
    if (!Config)
    {
        return nullptr;
    }

    return Config->Bookmarks.FindByPredicate(
        [BookmarkId](const FRaftSimReplayDebugBookmark& Bookmark)
        {
            return Bookmark.BookmarkId == BookmarkId;
        });
}

float URaftSimReplayDebugViewerViewModel::GetMaxPlaybackTimeSeconds() const
{
    if (!Config || Config->FrameCount <= 0)
    {
        return 0.0f;
    }

    return static_cast<float>(Config->FrameCount - 1) * Config->FixedDeltaSeconds;
}
