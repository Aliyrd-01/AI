import subprocess, sys, os

PS = r"""
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.GetInstalledVoices() | ForEach-Object {
  Write-Output ($_.VoiceInfo.Name + ' | ' + $_.VoiceInfo.Culture)
}
"""
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_list_voices.ps1")
with open(p, "w", encoding="utf-8") as f:
    f.write(PS)
r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", p],
                   capture_output=True, text=True)
print(r.stdout)
if r.returncode != 0:
    print("ERR:", r.stderr[:400])
