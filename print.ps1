# 監視するフォルダのパス
$folderToWatch = "outputs"
# 印刷後に移動させるフォルダのパス
$printedFolder = "outputs//printed"
# 最大再試行回数
$maxRetry = 3

# ファイルが作成されたときの処理
$action = {
    $file = $Event.SourceEventArgs.Name
    $path = $Event.SourceEventArgs.FullPath
    
    $retryPrintCount = 0

    while ($retryPrintCount -lt $maxRetry) {
        try {
            # 印刷ジョブをキューに追加する
            Start-Process -FilePath "mspaint.exe" -ArgumentList "/p `"$path`"" -NoNewWindow -Wait
            Write-Host "印刷ジョブがキューに追加されました。$file"
            break  # 印刷成功したらループを終了してファイル移動処理へ
        }
        catch {
            Write-Host "印刷エラーが発生しました。再試行します。　エラー: $_"
            $retryPrintCount++
            Start-Sleep -Seconds 2  # 再試行の間隔
        }
    }
    
    if ($retryPrintCount -eq $maxRetry) {
        Write-Host "印刷エラー。ファイルをスキップします。ファイル名：$file"
        return  # 失敗した場合、次のファイルの処理に進む
    }

    # 印刷後、ファイルを別のフォルダに移動する
    $moveSuccess = $false
    $retryMoveCount = 0

    while (-not $moveSuccess -and $retryMoveCount -lt $maxRetry) {
        try {
            Move-Item -Path $path -Destination $printedFolder -ErrorAction Stop
            $moveSuccess = $true
        }
        catch {
            Write-Host "ファイルの移動エラー。再試行します。エラーメッセージ: $_"
            $retryMoveCount++
            Start-Sleep -Seconds 2  # 再試行の間隔
        }
    }

    if (-not $moveSuccess) {
        Write-Host "ファイルの移動に失敗しました。"
        # 移動できない場合のエラー処理を追加する
    }
}

# イベントを登録する
$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = $folderToWatch
$watcher.Filter = "*.jpg"  # 画像ファイルの拡張子を指定
Register-ObjectEvent -InputObject $watcher -EventName Created -SourceIdentifier FileCreated -Action $action > $null

# 終了するまでスクリプトを実行し続ける
try {
    while ($true) {
        # 無限ループを維持してスクリプトが実行されることを保証
        # Ctrl+C で中断するまで監視を続ける
        Start-Sleep -Seconds 1
    }
}
finally {
    # 監視を停止する
    Unregister-Event -SourceIdentifier FileCreated
}
