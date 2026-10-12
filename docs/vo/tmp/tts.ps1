Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.SelectVoice('Microsoft Zira Desktop')
$synth.SetOutputToWaveFile('<root>\portfolio\docs\vo\en_unified_agent.wav')
$text = Get-Content -Raw -Encoding UTF8 '<root>\portfolio\docs\vo\tmp\text.txt'
$synth.Speak($text)
$synth.Dispose()
