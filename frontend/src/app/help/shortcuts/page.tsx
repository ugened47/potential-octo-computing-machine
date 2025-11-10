"use client";

import Link from "next/link";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Keyboard } from "lucide-react";

const shortcuts = [
  {
    category: "Navigation",
    items: [
      { keys: ["G", "D"], description: "Go to Dashboard" },
      { keys: ["G", "U"], description: "Go to Upload" },
      { keys: ["G", "H"], description: "Go to Help" },
      { keys: ["/"], description: "Focus search" },
    ],
  },
  {
    category: "Video Player",
    items: [
      { keys: ["Space"], description: "Play/Pause" },
      { keys: ["→"], description: "Seek forward 5 seconds" },
      { keys: ["←"], description: "Seek backward 5 seconds" },
      { keys: ["↑"], description: "Increase volume" },
      { keys: ["↓"], description: "Decrease volume" },
      { keys: ["M"], description: "Mute/Unmute" },
      { keys: ["F"], description: "Fullscreen" },
    ],
  },
  {
    category: "Timeline Editor",
    items: [
      { keys: ["Ctrl", "Z"], description: "Undo" },
      { keys: ["Ctrl", "Y"], description: "Redo" },
      { keys: ["Ctrl", "S"], description: "Save segments" },
      { keys: ["+"], description: "Zoom in" },
      { keys: ["-"], description: "Zoom out" },
      { keys: ["Delete"], description: "Delete selected segment" },
    ],
  },
  {
    category: "General",
    items: [
      { keys: ["Esc"], description: "Close dialog/modal" },
      { keys: ["?"], description: "Show keyboard shortcuts" },
    ],
  },
];

function KeyBadge({ key: keyValue }: { key: string }) {
  return (
    <kbd className="px-2 py-1 text-xs font-semibold text-gray-800 bg-gray-100 border border-gray-200 rounded-lg dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600">
      {keyValue}
    </kbd>
  );
}

export default function KeyboardShortcutsPage() {
  return (
    <div className="container mx-auto py-8 max-w-4xl">
      <div className="mb-8">
        <Link href="/help">
          <Button variant="ghost" className="mb-4">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Help
          </Button>
        </Link>
        <div className="flex items-center gap-3 mb-2">
          <Keyboard className="h-8 w-8" />
          <h1 className="text-3xl font-bold">Keyboard Shortcuts</h1>
        </div>
        <p className="text-muted-foreground">
          Speed up your workflow with these keyboard shortcuts.
        </p>
      </div>

      <div className="space-y-6">
        {shortcuts.map((category, categoryIndex) => (
          <Card key={categoryIndex}>
            <CardHeader>
              <CardTitle>{category.category}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {category.items.map((item, itemIndex) => (
                  <div
                    key={itemIndex}
                    className="flex items-center justify-between py-2 border-b last:border-0"
                  >
                    <span className="text-sm">{item.description}</span>
                    <div className="flex items-center gap-1">
                      {item.keys.map((key, keyIndex) => (
                        <span
                          key={keyIndex}
                          className="flex items-center gap-1"
                        >
                          <KeyBadge key={key} />
                          {keyIndex < item.keys.length - 1 && (
                            <span className="text-muted-foreground mx-1">
                              +
                            </span>
                          )}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="mt-8">
        <Card>
          <CardHeader>
            <CardTitle>Tip</CardTitle>
            <CardDescription>
              Press <KeyBadge key="?" /> anywhere in the app to see this list of
              shortcuts.
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    </div>
  );
}
