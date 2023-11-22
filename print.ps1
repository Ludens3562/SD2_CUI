# �Ď�����t�H���_�̃p�X
$folderToWatch = "outputs"
# �����Ɉړ�������t�H���_�̃p�X
$printedFolder = "outputs//printed"
# �ő�Ď��s��
$maxRetry = 3

# �t�@�C�����쐬���ꂽ�Ƃ��̏���
$action = {
    $file = $Event.SourceEventArgs.Name
    $path = $Event.SourceEventArgs.FullPath
    
    $retryPrintCount = 0

    while ($retryPrintCount -lt $maxRetry) {
        try {
            # ����W���u���L���[�ɒǉ�����
            Start-Process -FilePath "mspaint.exe" -ArgumentList "/p `"$path`"" -NoNewWindow -Wait
            Write-Host "����W���u���L���[�ɒǉ�����܂����B$file"
            break  # ������������烋�[�v���I�����ăt�@�C���ړ�������
        }
        catch {
            Write-Host "����G���[���������܂����B�Ď��s���܂��B�@�G���[: $_"
            $retryPrintCount++
            Start-Sleep -Seconds 2  # �Ď��s�̊Ԋu
        }
    }
    
    if ($retryPrintCount -eq $maxRetry) {
        Write-Host "����G���[�B�t�@�C�����X�L�b�v���܂��B�t�@�C�����F$file"
        return  # ���s�����ꍇ�A���̃t�@�C���̏����ɐi��
    }

    # �����A�t�@�C����ʂ̃t�H���_�Ɉړ�����
    $moveSuccess = $false
    $retryMoveCount = 0

    while (-not $moveSuccess -and $retryMoveCount -lt $maxRetry) {
        try {
            Move-Item -Path $path -Destination $printedFolder -ErrorAction Stop
            $moveSuccess = $true
        }
        catch {
            Write-Host "�t�@�C���̈ړ��G���[�B�Ď��s���܂��B�G���[���b�Z�[�W: $_"
            $retryMoveCount++
            Start-Sleep -Seconds 2  # �Ď��s�̊Ԋu
        }
    }

    if (-not $moveSuccess) {
        Write-Host "�t�@�C���̈ړ��Ɏ��s���܂����B"
        # �ړ��ł��Ȃ��ꍇ�̃G���[������ǉ�����
    }
}

# �C�x���g��o�^����
$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = $folderToWatch
$watcher.Filter = "*.jpg"  # �摜�t�@�C���̊g���q���w��
Register-ObjectEvent -InputObject $watcher -EventName Created -SourceIdentifier FileCreated -Action $action > $null

# �I������܂ŃX�N���v�g�����s��������
try {
    while ($true) {
        # �������[�v���ێ����ăX�N���v�g�����s����邱�Ƃ�ۏ�
        # Ctrl+C �Œ��f����܂ŊĎ��𑱂���
        Start-Sleep -Seconds 1
    }
}
finally {
    # �Ď����~����
    Unregister-Event -SourceIdentifier FileCreated
}
