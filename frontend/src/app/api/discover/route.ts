
import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import path from 'path';

export async function POST(request: Request) {
  try {
    const rootDir = process.cwd();
    // Assuming the script is at src/discovery/run_discovery.py relative to the project root
    // Since we are in frontend/, we need to go up one level
    const scriptPath = path.resolve(rootDir, '../src/discovery/run_discovery.py');
    const venvPython = path.resolve(rootDir, '../venv/bin/python'); // Or 'python' if in global env

    console.log(`Starting discovery process: ${venvPython} ${scriptPath}`);

    // Run in background (don't wait for full completion to respond, 
    // but maybe we should return "Started" and let frontend poll? 
    // For now, let's keep it simple and just run it.)
    
    // We execute this command. It might take a while.
    exec(`${venvPython} ${scriptPath}`, { cwd: path.resolve(rootDir, '..') }, (error, stdout, stderr) => {
        if (error) {
            console.error(`Discovery exec error: ${error}`);
            return;
        }
        console.log(`Discovery stdout: ${stdout}`);
        console.error(`Discovery stderr: ${stderr}`);

        // After discovery finishes, we should merge the leads
        exec(`${venvPython} scripts/merge_leads.py`, { cwd: path.resolve(rootDir, '..') }, (mergeError, mergeStdout, mergeStderr) => {
             if (mergeError) {
                console.error(`Merge exec error: ${mergeError}`);
             }
             console.log("Merge completed");
        });
    });

    return NextResponse.json({ 
        message: 'Discovery process started successfully. Check back in a few minutes!',
        status: 'started'
    });

  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json(
      { error: 'Failed to start discovery process' },
      { status: 500 }
    );
  }
}
